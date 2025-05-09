from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.post("/login")
def login() -> dict[str, str]:
    return {"message": "Login successful"}


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"message": "Logout successful"}
