from fastapi import Depends, APIRouter, Body
from starlette.status import HTTP_201_CREATED

from backend.app.api.dependencies.database import get_repository
from backend.app.db.repositories.users import UsersRepository
from backend.app.models.token import AccessToken
from backend.app.models.user import UserCreate, UserPublic
from backend.app.services import auth_service

router = APIRouter()


@router.post("/", response_model=UserPublic, name="users:register-new-user", status_code=HTTP_201_CREATED)
async def register_new_user(
        new_user: UserCreate = Body(..., embed=True),
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    created_user = await user_repo.register_new_user(new_user=new_user)
    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user), token_type="bearer"
    )
    return UserPublic(**created_user.dict(), access_token=access_token)
