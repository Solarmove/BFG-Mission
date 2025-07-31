import asyncio
import logging

import backoff
import openai
from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import BaseDialogManager, DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_i18n import I18nContext
from arq import ArqRedis
from langchain_openai import ChatOpenAI
from openai import RateLimitError
from redis.asyncio import Redis
from tenacity import retry, wait_random_exponential, stop_after_attempt

from ...services.ai_agent.main import AIAgent
from ...services.ai_agent.prompts import get_prompt_from_hierarchy_level, get_prompt
from ...services.ai_agent.tools_manager import Tools
from ...services.log_service import LogService
from ...utils.misc import voice_to_text
from ...utils.unitofwork import UnitOfWork
from . import states


logger = logging.getLogger(__name__)


