"""Tech Stack Intel — detect technologies used by websites."""

from techstack_intel.analyzer import analyze
from techstack_intel.models import DetectedTechnology, TechStackReport

__all__ = ["analyze", "DetectedTechnology", "TechStackReport"]
