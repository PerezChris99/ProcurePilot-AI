"""Never run real E2E registration against production or unknown Neon."""
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"qa"))
from staging_e2e import STAGING_HOST, require_staging

def test_exact_staging_target_is_permitted():
    require_staging("postgresql://owner:placeholder@"+STAGING_HOST+"/procurepilot?sslmode=require")

@pytest.mark.parametrize("uri",[
    "postgresql://owner:pw@ep-blue-band-bcjqtqrc.c-16.us-east-1.aws.neon.tech/procurepilot?sslmode=require",
    "postgresql://owner:pw@localhost/procurepilot?sslmode=require",
    "postgresql://owner:pw@"+STAGING_HOST+"/other?sslmode=require",
])
def test_all_non_staging_targets_rejected(uri):
    with pytest.raises(ValueError):require_staging(uri)
