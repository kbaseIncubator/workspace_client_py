
class WorkspaceResponseError(RuntimeError):
    """An unsuccessful workspace request was made."""

    def __init__(self, resp):
        self.resp_text = resp.text
        self.status_code = resp.status_code
        try:
            self.resp_data = resp.json()
        except Exception:
            self.resp_data = None

    def __str__(self):
        msg = self.resp_data['error']['message']
        return f"Workspace error with code {self.status_code}\n  {msg}"


class UnauthorizedShockDownload(RuntimeError):
    """The user does not have access to this shock file."""

    def __init__(self, id_):
        self.id = id_

    def __str__(self):
        return "Unauthorized access to shock file with ID " + self.id


class MissingShockFile(RuntimeError):
    """There is no shock file for the given shock ID."""

    def __init__(self, id_):
        self.id = id_

    def __str__(self):
        return "Missing shock file with ID " + self.id
