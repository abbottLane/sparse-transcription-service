"""With relation dbs, it would be typical to interact with database via ORM, 
In which case data validation would be modeled like this:"""

from typing import Optional
from pydantic import BaseModel
from pydantic.types import StrBytes, List


class ILanguage(BaseModel):
    name: str
    iso639_2: Optional[str]
    glottocode: Optional[str]


class NBaseModel(BaseModel):
    def __getitem__(self, item):
        return getattr(self, item)


class CreateProjectModel(NBaseModel):
    name: str
    owner: str
    date: int
    glossary_id: str
    glossary_langs: List[ILanguage]
    metadata: Optional[dict]
    project_body: Optional[dict]

    class Config:
        schema_extra = {
            "example": {
                "name": "My Kunwinjku Tours project",
                "owner": "William Lane",
                "date": 161369422282,
                "glossary_id": "2",
                "glossary_langs": [{"name": "kunwinjku", "iso639_2": "gup"}],
                "metadata": {},
                "project_body": {}
            }
        }

    def __getitem__(self, item):
        return getattr(self, item)


class CreateTokenModel(BaseModel):
    breath_group_id: str
    project_id: str
    confidence: Optional[float]
    start: Optional[float]
    stop: Optional[float]
    duration: Optional[float]

    def __getitem__(self, item):
        return getattr(self, item)


class CreateGlossaryEntryModel(NBaseModel):
    form: str
    gloss: str
    tokens: List
    user: str
    canonical: bool
    glossary_id: str
    lexical_entry: Optional[dict]


class UpsertTokenModel(NBaseModel):
    form: str
    user: str
    canonical: bool
    glossary_id: str
    breath_group_id: str
    project_id: str
    media_id: str
    position: Optional[int]

class RemoveTokenModel(NBaseModel):
    user: str
    glossary_id: str
    glossary_entry_id: str
    breath_group_id: str
    project_id: str
    token_id: str
    media_id: str

class CreateGlossaryModel(BaseModel):
    name: str
    language: List[ILanguage]

    class Config:
        schema_extra = {
            "example": {
                "name": "KunwinjkuM",
                "language": [{"name": "kunwinjku", "iso639_2": "gup"}],
            }
        }

    def __getitem__(self, item):
        return getattr(self, item)


class CreateMediaModel(NBaseModel):
    mimetype: str
    name: str
    project: str
    metadata: Optional[dict]

    class Config:
        schema_extra = {
            "example": {
                "mimetype": "audio/x-wav",
                "name": "MIXPRE-01930-WL",
                "project": "60234d46799943ad297b0063",
                "metadata": {}
            }
        }


class GetProjectInfoModel(NBaseModel):
    id: str
    name: str
    owner: str
    date: int
    glossary_id: str
    glossary_langs: List[ILanguage]
    metadata: Optional[dict]

    class Config:
        schema_extra = {
            "id": "6032f8faef6ddb0fa98d6cac",
            "name": "My Kunwinjku Tours project",
            "owner": "William Lane",
            "date": 161369422,
            "glossary_id": "2",
            "glossary_langs": [
                {
                    "name": "kunwinjku",
                    "iso639_2": "gup",
                    "glottocode": None
                }
            ],
            "metadata": {}
        }


class GetProjectModel(NBaseModel):
    id: str
    name: str
    owner: str
    date: int
    glossary_id: str
    glossary_langs: List[ILanguage]
    metadata: Optional[dict]
    project_body: Optional[dict]


class GetMediaModel(NBaseModel):
    mimetype: str
    name: str
    project: str
    processed: bool
    metadata: Optional[dict]


class GetGlossaryModel(NBaseModel):
    name: str
    language: List[ILanguage]
    entries: Optional[dict]


class AlignPhonesModel(NBaseModel):
    tokens: List[str]
    phones: str

    class Config:
        schema_extra = {
            "tokens": ['birri', 'mane'],
            "phones": "m ɐ n ʊ ŋ l ʊ d ɔ l ɐ t ɔ k ɐ b ɪ r ɪ m ɐ n b ɔ n"
        }


class AlignedToken(NBaseModel):
    token: str
    start: int
    stop: int

    class Config:
        schema_extra = {
            "token": "birri",
            "start": 15,
            "stop": 18
        }


class DiscoverWordsModel(NBaseModel):
    phone_str: str
    aligned_tokens: List[AlignedToken]

    class Config:
        schema_extra = {
            "phone_str": "m ɐ n ʊ ŋ l ʊ d ɔ l ɐ t ɔ k ɐ b ɪ r ɪ m ɐ n b ɔ n",
            "aligned_tokens": [
                {
                    "token": "birri",
                    "start": 15,
                    "stop": 18
                },
                {
                    "token": "mane",
                    "start": 0,
                    "stop": 3
                }
            ]
        }


class UserLoginModel(NBaseModel):
    displayName: str
    uid: str
    email: str
    photoURL: str


def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    return {
        "error": error,
        "code": code,
        "message": message
    }
