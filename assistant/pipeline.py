"""Application pipeline, independent of terminal input and concrete feature engines."""
from .models import Response, Session, CommandUnavailableError
from .router import route
from .dispatch import dispatch


class AssistantPipeline:
    def __init__(self, *, session=None, emit=None, resolve=None):
        self.session = session if session is not None else Session()
        self.emit = emit if emit is not None else lambda text: None
        self.resolve = resolve

    def handle(self, command):
        """Route and execute a text command; return a response without forced TTS."""
        try:
            return dispatch(route(command, self.session.pending_action), self.session,
                            emit=self.emit, resolve=self.resolve)
        except CommandUnavailableError as error:
            return Response(str(error))
        except ImportError as error:
            print("Feature dependency error:", error)
            return Response("This feature needs an unavailable dependency. Install requirements.txt in your active environment.")
        except Exception as error:
            print("Command processing error:", error)
            return Response("Sorry, something went wrong while processing your command.")

    def step(self, command):
        response = self.handle(command)
        if response.text:
            self.emit(response.text)
        return response.continue_running
