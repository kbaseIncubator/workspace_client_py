
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
        return f"Workspace error with code {self.status_code}:\n{self.resp_text}"


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


class InvalidUser(Exception):
    """Invalid token for user; cannot authenticate."""
    pass


class InaccessibleWSObject(Exception):
    """A workspace object is inaccessible to the user."""
    pass


class InvalidWSType(Exception):

    def __init__(self, given, valid_types):
        self.given = given
        self.valid_types = valid_types

    def __str__(self):
        types = ", ".join(self.valid_types)
        return "Invalid workspace type: " + self.given + ". Valid types are: " + types


class FileExists(Exception):
    """A file already exists at a path where we want to download something."""
    pass


class InvalidGenome(Exception):
    """The genome object does not have the right data structure for download."""
    pass


class InvalidWSResponse(Exception):

    def __init__(self, response_text):
        self.resp = response_text

    def __str__(self):
        return "Invalid response from the workspace:\n%s" % self.resp
