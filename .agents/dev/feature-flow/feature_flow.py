"""
type: workflow
description: Develop an MDXCanvas feature from discovery through release.
usage: no arguments
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHARED_WORKFLOW_DIRECTORY = PROJECT_ROOT.parent / "rosters/development/feature-flow"
sys.path.insert(0, str(SHARED_WORKFLOW_DIRECTORY))

from feature_flow import main


if __name__ == "__main__":
    main(PROJECT_ROOT / ".agents/project.md")
