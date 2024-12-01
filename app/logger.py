# app/logger.py
import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#     handlers=[
#         logging.FileHandler("app.log"),
#         logging.StreamHandler()
#     ]
# )

# logger = logging.getLogger(__name__)

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('app.log')
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
c_format = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
f_format = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)