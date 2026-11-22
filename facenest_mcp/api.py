"""Thin HTTP client for FaceNest's local `/mcp/*` endpoints (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .endpoint import Endpoint


class FaceNestError(RuntimeError):
    """An error reported by the app. `code` is a language-neutral `ERR_*`; `message` is the app's own fallback text."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message or f"HTTP {status}")
        self.status = status
        self.code = code


class Client:
    def __init__(self, endpoint: Endpoint, timeout: float = 20.0,
                 endpoint_path: Optional[str] = None):
        self.endpoint = endpoint
        self.timeout = timeout
        # FaceNest picks a random port and a fresh token on every start. A
        # long-lived MCP process that cached the old endpoint would keep showing
        # "cannot connect". Remembering the file path lets one re-read heal it.
        self.endpoint_path = endpoint_path
        # When the endpoint file was unreadable at startup (FaceNest not
        # running / MCP off), the server no longer exits — it keeps serving with
        # this reason, so each call can report something actionable.
        self.deferred_reason = ""

    def refresh_endpoint(self) -> bool:
        """Re-read the endpoint file; True on success.

        Without an explicit path this falls back to **auto-discovery**
        (`load_endpoint(None)`) — clients often point at no path at all and the
        file simply appears later.
        """
        try:
            from .endpoint import load_endpoint
            self.endpoint = load_endpoint(self.endpoint_path or None)
            return True
        except Exception:  # noqa: BLE001
            return False

    # -- internals ---------------------------------------------------------
    def _request(self, method: str, path: str,
                 params: Optional[Dict[str, Any]] = None,
                 body: Optional[Dict[str, Any]] = None,
                 _retried: bool = False,
                 timeout: Optional[float] = None) -> Dict[str, Any]:
        # No usable endpoint yet (port 0 = placeholder) => every call first
        # tries to re-read the file. So after the user turns MCP on inside
        # FaceNest, **the next tool call works** — no client restart, no new session.
        if not int(getattr(self.endpoint, "port", 0) or 0) and not self.refresh_endpoint():
            raise FaceNestError(
                0, "ERR_MCP_NOT_READY",
                self.deferred_reason
                or "mcp_endpoint.json is not there yet: FaceNest is not running, or the MCP service is off.")
        url = self.endpoint.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-FaceNest-Token", self.endpoint.token)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        wait = self.timeout if timeout is None else timeout
        try:
            with urllib.request.urlopen(req, timeout=wait) as resp:
                return json.loads(resp.read().decode("utf-8") or "{}")
        except TimeoutError as exc:
            # Loading the semantic model for the first time takes longer than the
            # usual 20s budget. This used to raise a bare TimeoutError, which
            # surfaced as JSON-RPC -32603 and the agent read it as "tool broken".
            raise FaceNestError(
                0, "ERR_MCP_TIMEOUT",
                f"FaceNest did not answer within {wait:.0f}s "
                f"({self.endpoint.base_url}{path}): {exc}") from None
        except urllib.error.HTTPError as exc:
            raw = ""
            try:
                raw = exc.read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                pass
            detail = raw
            try:
                detail = json.loads(raw).get("detail", raw)
            except Exception:  # noqa: BLE001
                pass
            code, _, prose = str(detail).partition("|")
            if not code.startswith("ERR_"):
                code, prose = "ERR_HTTP", str(detail)
            if code == "ERR_MCP_TOKEN" and not _retried and self.refresh_endpoint():
                try:
                    return self._request(method, path, params, body,
                                         _retried=True, timeout=timeout)
                except FaceNestError:
                    pass
            raise FaceNestError(exc.code, code, prose) from None
        except urllib.error.URLError as exc:
            if not _retried and self.refresh_endpoint():
                try:
                    return self._request(method, path, params, body,
                                         _retried=True, timeout=timeout)
                except FaceNestError:
                    pass
            raise FaceNestError(
                0, "ERR_UNREACHABLE",
                f"Cannot reach FaceNest at {self.endpoint.base_url}: {exc.reason}. "
                "Is the app running, and is the MCP service enabled?") from None

    def place_tree(self) -> Dict[str, Any]:
        """Geographic tree with photo counts (only photos that carry GPS)."""
        return self._request("GET", "/places/tree")

    def photos_in_place(self, country: Optional[str] = None,
                        admin1: Optional[str] = None, city: Optional[str] = None,
                        limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        return self._request("GET", "/places/images",
                             params={"country": country, "admin1": admin1,
                                     "city": city, "limit": limit, "offset": offset})

    def find_duplicates(self, mode: str = "exact", threshold: Optional[int] = None,
                        time_window: Optional[int] = None,
                        pixel_verify: bool = True) -> Dict[str, Any]:
        params: Dict[str, Any] = {"mode": mode}
        if threshold is not None:
            params["threshold"] = threshold
        if time_window is not None:
            params["time_window"] = time_window
        if mode == "similar":
            params["pixel_verify"] = "true" if pixel_verify else "false"
        return self._request("GET", "/duplicates", params=params)

    # -- tools -------------------------------------------------------------
    def ping(self) -> Dict[str, Any]:
        return self._request("GET", "/mcp/ping")

    def search(self, q: str, mode: str = "all", limit: int = 20,
               compact: bool = False) -> Dict[str, Any]:
        params: Dict[str, Any] = {"q": q, "mode": mode, "limit": limit}
        if compact:
            params["compact"] = "true"
        return self._request("GET", "/mcp/search", params=params)

    def image_context(self, image_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/mcp/images/{urllib.parse.quote(image_id)}")

    def query_photos(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Read-only rule query: the same rule grammar as a smart album, without creating one."""
        return self._request("POST", "/mcp/query", body=payload)

    def list_tags(self, q: Optional[str] = None, source: str = "any",
                  limit: int = 100) -> Dict[str, Any]:
        """Tags that really exist in the library, with counts (this lets an agent discover the vocabulary instead of guessing)."""
        return self._request("GET", "/mcp/tags",
                             params={"q": q, "source": source, "limit": limit})

    def similar_photos(self, image_id: Optional[str] = None,
                       image_path: Optional[str] = None,
                       limit: int = 50) -> Dict[str, Any]:
        """Find-photos-by-image: give exactly one reference — a library image_id, or a local image_path."""
        body: Dict[str, Any] = {"limit": int(limit)}
        if image_id:
            body["image_id"] = image_id
        if image_path:
            body["image_path"] = image_path
        return self._request("POST", "/mcp/similar-photos", body=body,
                             timeout=60.0)

    def list_smart_albums(self) -> Dict[str, Any]:
        return self._request("GET", "/mcp/smart-albums")

    def list_albums(self, limit: int = 500, offset: int = 0,
                    album_id: Optional[int] = None,
                    photos: bool = False) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if album_id is not None:
            params["album_id"] = int(album_id)
        if photos:
            params["photos"] = "true"
        return self._request("GET", "/mcp/albums", params=params)

    def smart_album_images(self, smart_id: int, limit: int = 50,
                           offset: int = 0, compact: bool = False) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if compact:
            params["compact"] = "true"
        return self._request("GET", f"/mcp/smart-albums/{int(smart_id)}/images",
                             params=params)

    def create_smart_album(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/mcp/smart-albums", body=payload)

    def semantic_search(self, text: str, limit: int = 50,
                        compact: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"text": text, "limit": limit}
        if compact:
            body["compact"] = True
        return self._request("POST", "/mcp/semantic-search",
                             body=body, timeout=60.0)

    def update_smart_album(self, smart_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/mcp/smart-albums/{int(smart_id)}", body=payload)

    def delete_smart_album(self, smart_id: int) -> Dict[str, Any]:
        """Delete the album definition only (the smart_albums row); returns a snapshot so it can be rebuilt as-is."""
        return self._request("DELETE", f"/mcp/smart-albums/{int(smart_id)}")

    # -- people / video -------------------------------------------------------
    def list_people(self, include_unnamed: bool = False, limit: int = 50,
                    offset: int = 0) -> Dict[str, Any]:
        return self._request("GET", "/mcp/people",
                             params={"include_unnamed": str(bool(include_unnamed)).lower(),
                                     "limit": limit, "offset": offset})

    def person_photos(self, cluster_id: int, limit: int = 50,
                      offset: int = 0, compact: bool = False) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if compact:
            params["compact"] = "true"
        return self._request("GET", f"/mcp/people/{int(cluster_id)}/photos",
                             params=params)

    def similar_faces(self, image_id: Optional[str] = None,
                      face_id: Optional[str] = None,
                      threshold: Optional[float] = None,
                      limit: Optional[int] = None,
                      image_path: Optional[str] = None,
                      face_index: Optional[int] = None,
                      offset: Optional[int] = None,
                      person: Optional[str] = None) -> Dict[str, Any]:
        """Reference is one of: `image_id` / `image_path` (a local path) / `face_id` (library or video index).

        `face_id` may be used on its own; `face_index` picks one face of the
        reference image (left -> right) when nobody has been named yet.
        """
        body: Dict[str, Any] = {}
        if image_id:
            body["image_id"] = image_id
        if image_path:
            body["image_path"] = image_path
        if face_id:
            body["face_id"] = face_id
        if face_index is not None:
            body["face_index"] = int(face_index)
        if threshold is not None:
            body["threshold"] = threshold
        if limit is not None:
            body["limit"] = limit
        if offset is not None:
            body["offset"] = int(offset)
        if person:
            body["person"] = str(person)
        return self._request("POST", "/mcp/similar-faces", body=body)

    def list_videos(self, limit: int = 50) -> Dict[str, Any]:
        return self._request("GET", "/mcp/videos", params={"limit": limit})

    def find_person_in_videos(self, cluster_id: Optional[int] = None,
                              face_id: Optional[str] = None,
                              threshold: Optional[float] = None,
                              limit: Optional[int] = None,
                              video_id: Optional[str] = None,
                              order: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if cluster_id is not None:
            body["cluster_id"] = int(cluster_id)
        if face_id:
            body["face_id"] = face_id
        if threshold is not None:
            body["threshold"] = threshold
        if limit is not None:
            body["limit"] = limit
        if video_id:
            body["video_id"] = video_id
        if order:
            body["order"] = order
        return self._request("POST", "/mcp/videos/find", body=body)

    def collect_video_frame(self, video_id: str, timestamp_sec: float) -> Dict[str, Any]:
        return self._request("POST", "/mcp/videos/collect-frame",
                             body={"video_id": video_id,
                                   "timestamp_sec": float(timestamp_sec)})

    # -- video picking: frame timeline / pick best / batch collect -------------
    def video_frames(self, video_id: str, from_sec: Optional[float] = None,
                     to_sec: Optional[float] = None, limit: int = 50,
                     offset: int = 0, with_faces: bool = True) -> Dict[str, Any]:
        return self._request(
            "GET", "/mcp/videos/%s/frames" % urllib.parse.quote(video_id),
            params={"from_sec": from_sec, "to_sec": to_sec, "limit": int(limit),
                    "offset": int(offset),
                    "with_faces": "true" if with_faces else "false"})

    def pick_best_video_frames(self, **kwargs) -> Dict[str, Any]:
        """Reference + preset / prefer_smiling / top; see the tool schema."""
        body = {k: v for k, v in kwargs.items() if v is not None}
        return self._request("POST", "/mcp/videos/pick-best", body=body,
                             timeout=120.0)

    def collect_video_frames(self, frame_ids: Optional[List[str]] = None,
                             items: Optional[List[Dict[str, Any]]] = None,
                             album_name: Optional[str] = None,
                             dry_run: bool = False) -> Dict[str, Any]:
        body: Dict[str, Any] = {"dry_run": bool(dry_run)}
        if frame_ids:
            body["frame_ids"] = list(frame_ids)
        if items:
            body["items"] = list(items)
        if album_name:
            body["album_name"] = album_name
        return self._request("POST", "/mcp/videos/collect-frames", body=body,
                             timeout=120.0)

    def pick_best_photos(self, scope: Dict[str, Any], top: int = 3,
                         wait_sec: Optional[float] = 20,
                         min_face_px: Optional[int] = 64,
                         job_id: Optional[str] = None,
                         refresh: bool = False,
                         mode: str = "smile",
                         aspect: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"scope": scope, "top": int(top),
                                "mode": str(mode or "smile")}
        if refresh:
            body["refresh"] = True
        if wait_sec is not None:
            body["wait_sec"] = float(wait_sec)
        if min_face_px is not None:
            body["min_face_px"] = int(min_face_px)
        if job_id:
            body["job_id"] = job_id
        if aspect:
            body["aspect"] = str(aspect)
        wait = float(wait_sec if wait_sec is not None else 20) + 15.0
        return self._request("POST", "/mcp/photos/pick-best", body=body,
                             timeout=wait)

    def copy_photos(self, image_ids: List[str], target_dir: str,
                    rename_pattern: Optional[str] = None,
                    overwrite: bool = False) -> Dict[str, Any]:
        """Copy original bytes into the user's folder (write gate in the app)."""
        body: Dict[str, Any] = {"image_ids": list(image_ids),
                                "target_dir": str(target_dir)}
        if rename_pattern:
            body["rename_pattern"] = str(rename_pattern)
        if overwrite:
            body["overwrite"] = True
        return self._request("POST", "/mcp/photos/copy-to", body=body,
                             timeout=120.0)

    def contact_sheet(self, image_ids: List[str],
                      title: Optional[str] = None) -> Dict[str, Any]:
        """Build a numbered thumbnail wall; the returned URL is the credential."""
        body: Dict[str, Any] = {"image_ids": list(image_ids)}
        if title:
            body["title"] = str(title)
        return self._request("POST", "/mcp/contact-sheet", body=body, timeout=60.0)
