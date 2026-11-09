
from fastapi import APIRouter, HTTPException,Depends
from authen.auth import verify_token 
from pydantic import BaseModel, Field

from services.announcements import  create_announcement, update_announcement,approve_announcement,   reject_announcement
   
   
    
 



# ==========================================
# Router
# ==========================================
router = APIRouter(dependencies=[Depends(verify_token)],
    prefix="/announcements",
    tags=["Announcements"]
)


# ==========================================
# Request Models
# ==========================================

class GenerateAnnouncementRequest(BaseModel):

    designation: str

    prompt: str = Field(
        min_length=1,
        max_length=5000
    )


class ModifyAnnouncementRequest(BaseModel):

    designation: str

    existing_announcement: str = Field(
        min_length=1,
        max_length=10000
    )

    modification_prompt: str = Field(
        min_length=1,
        max_length=3000
    )


class ApproveAnnouncementRequest(BaseModel):

    designation: str

    title: str = Field(
        min_length=1,
        max_length=200
    )

    announcement: str = Field(
        min_length=1,
        max_length=10000
    )


class RejectAnnouncementRequest(BaseModel):

    designation: str

    title: str = Field(
        min_length=1,
        max_length=200
    )

    announcement: str = Field(
        min_length=1,
        max_length=10000
    )


# ==========================================
# Generate Announcement
# ==========================================

@router.post("/generate")
def generate_announcement(
    request: GenerateAnnouncementRequest
):

    try:

        print("\n========== GENERATE ==========")

        print("Designation:", request.designation)

        print("Prompt:", request.prompt)

        result = create_announcement(
            designation=request.designation,
            prompt=request.prompt
        )

        print("Announcement generated successfully")

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("GENERATE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Announcement generation failed: {type(e).__name__}: {str(e)}"
        )


# ==========================================
# Modify Announcement
# ==========================================

@router.post("/modify")
def modify_announcement(
    request: ModifyAnnouncementRequest
):

    try:

        print("\n========== MODIFY ==========")

        result = update_announcement(
            designation=request.designation,
            existing_announcement=request.existing_announcement,
            modification_prompt=request.modification_prompt
        )

        print("Announcement modified successfully")

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("MODIFY ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Announcement modification failed: {type(e).__name__}: {str(e)}"
        )


# ==========================================
# Approve Announcement
# ==========================================

@router.post("/approve")
def approve_announcement_api(
    request: ApproveAnnouncementRequest
):

    try:

        print("\n========== APPROVE ==========")

        print("Designation:", request.designation)

        print("Title:", request.title)

        result = approve_announcement(
            designation=request.designation,
            title=request.title,
            announcement=request.announcement
        )

        print("Announcement approval completed")

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("APPROVE ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Announcement approval failed: {type(e).__name__}: {str(e)}"
        )


# ==========================================
# Reject Announcement
# ==========================================

@router.post("/reject")
def reject_announcement_api(
    request: RejectAnnouncementRequest
):

    try:

        print("\n========== REJECT ==========")

        result = reject_announcement(
            designation=request.designation,
            title=request.title,
            announcement=request.announcement
        )

        print("Announcement rejected")

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("REJECT ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Announcement rejection failed: {type(e).__name__}: {str(e)}"
        )
