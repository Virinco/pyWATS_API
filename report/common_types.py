from typing import TYPE_CHECKING, Any, Optional, Union, Literal, List, Annotated
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, model_validator, field_serializer
from abc import ABC, abstractmethod
from report.wats_base import WATSBase