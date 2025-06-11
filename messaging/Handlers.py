import MemoryHandler, ClientHandler, FunctionHandler, EngineHandler, ProjectorHandler, TimerHandler
from MemoryHandler import CMemoryHandler
from ClientHandler import CClientHandler
from FunctionHandler import CFunctionHandler
from ProjectorHandler import CProjectorHandler
from EngineHandler import CEngineHandler
from TimerHandler import CTimerHandler

from logger import _print

memoryhandler = CMemoryHandler()
clienthandler = CClientHandler()
functionhandler = CFunctionHandler()
projectorhandler = CProjectorHandler()
enginehandler = CEngineHandler()
timerhandler = CTimerHandler()

MESSAGE_SERVER_URL = "http://127.0.0.1:5002/process_messages"
MEMORY_SERVER_URL = "http://127.0.0.1:5003/process_messages"
CLIENT_SERVER_URL = "http://127.0.0.1:5000/process_messages"
FUNCTION_SERVER_URL = "http://127.0.0.1:5004/process_messages"
PROJECTOR_SERVER_URL = "http://127.0.0.1:5006/process_messages"
ENGINE_SERVER_URL = "http://127.0.0.1:5001/process_messages"
TIMER_SERVER_URL = "http://127.0.0.1:5005/process_messages"

CLIENT_HANDLER = "client"
MEMORY_HANDLER = "memory"
ENGINE_HANDLER = "engine"
FUNCTION_HANDLER = "functions"
PROJECTOR_HANDLER = "projector"
TIMER_HANDLER = "timer"

QUEUE_HANDLER_NAMES = [CLIENT_HANDLER, MEMORY_HANDLER, ENGINE_HANDLER, FUNCTION_HANDLER, PROJECTOR_HANDLER, TIMER_HANDLER]

CLIENT_HANDLER_INDEX = 0 
MEMORY_HANDLER_INDEX = 1
ENGINE_HANDLER_INDEX = 2
FUNCTION_HANDLER_INDEX = 3
PROJECTOR_HANDLER_INDEX = 4
TIMER_HANDLER_INDEX = 5

# it is very important that queue_hanlders have the same elements in the same order as their
# names in QUEUE_HANDLER_NAMES

queue_handlers = {}
queue_handlers[CLIENT_HANDLER] = tuple((clienthandler, "inout"))
queue_handlers[MEMORY_HANDLER] = tuple((memoryhandler, "outin"))
queue_handlers[ENGINE_HANDLER] = tuple((enginehandler, "outin"))
queue_handlers[FUNCTION_HANDLER] = tuple((functionhandler, "outin"))
queue_handlers[PROJECTOR_HANDLER] = tuple((projectorhandler, "outin"))
queue_handlers[TIMER_HANDLER] = tuple((timerhandler, "outin"))