from app.agents.word_discovery.word_discovery_service import initiate_discovery
from app.agents.phone_alignment.alignment_service import initiate_alignment
from fastapi import APIRouter
from app.data_access.schemas import DiscoverWordsModel, ResponseModel, AlignPhonesModel

router = APIRouter(
    tags=["Agents"],
    responses={404: {"description": "Not found"}},)

@router.post("/alignPhones/")
async def align_tokens_to_phones(task_data ):
    alignment = await initiate_alignment(task_data)
    return ResponseModel(alignment, "aligned tokens to phones")


@router.post("/wordDiscovery/")
async def word_discovery(task_data : DiscoverWordsModel):
    discovered = await initiate_discovery(task_data)
    return ResponseModel(discovered, "discovered stuff")
    