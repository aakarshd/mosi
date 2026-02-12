from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.schemas.analysis import AnalysisResponse, AnalysisSummaryResponse

router = APIRouter(tags=["analysis"])


@router.get("/{stock_id}", response_model=AnalysisResponse)
async def get_analysis(
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get full 11-point AI analysis for a stock."""
    # TODO: Wire to database query
    raise NotImplementedError


@router.get("/{stock_id}/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(
    stock_id: int,
    user: dict = Depends(get_current_user),
):
    """Get analysis summary — verdict, score, key highlights."""
    # TODO: Wire to database query
    raise NotImplementedError
