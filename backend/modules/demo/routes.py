from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from backend.modules.demo.service import prepare_preview

router = APIRouter(tags=["Demo"])


@router.get("/demo", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={"title": "Base de práctica"},
    )


@router.get("/preview", response_class=HTMLResponse)
def preview(request: Request, tema: str = Query(default="", max_length=80)) -> HTMLResponse:
    context = {"title": "Vista previa", "tema": prepare_preview(tema)}
    template = (
        "components/preview.html"
        if request.headers.get("HX-Request", "").lower() == "true"
        else "pages/preview.html"
    )
    return request.app.state.templates.TemplateResponse(
        request=request, name=template, context=context
    )
