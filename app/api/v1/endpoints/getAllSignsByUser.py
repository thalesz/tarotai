from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.personal_sign import PersonalSignSchemaBase
from app.schemas.planet import PlanetSchemaBase
from app.schemas.zodiac import ZodiacSchemaBase

router = APIRouter()


@router.get(
    "/signs",
    response_class=JSONResponse,
    summary="Retorna os signos por planeta do usuário",
    description="Retorna uma lista com cada planeta e o respectivo signo + grau do usuário (quando disponível).",
)
async def get_all_signs_by_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if not token_info or not getattr(token_info, "id", None):
            raise HTTPException(status_code=401, detail="Usuário não autenticado.")

        user_id = token_info.id

        planets = await PlanetSchemaBase.get_all_planet_ids_and_names(db)

        signs_summary = []
        def _parse_degree(value):
            """Tenta extrair um número float de `value` que pode ser float ou string com caracteres extras."""
            if value is None:
                return None
            # já é número
            try:
                return float(value)
            except Exception:
                pass
            # se for string, extrai primeiro número encontrado
            try:
                import re

                s = str(value)
                m = re.search(r"[-+]?[0-9]*\.?[0-9]+", s)
                if m:
                    return float(m.group(0))
            except Exception:
                return None
            return None

        for p in planets:
            planet_id = p.get("id")
            planet_name = p.get("name")
            sign_tuple = await PersonalSignSchemaBase.get_sign_and_degree_by_user_and_planet(db, user_id, planet_id)
            if sign_tuple:
                zodiac_id, degree_raw = sign_tuple
                zodiac_name = await ZodiacSchemaBase.get_zodiac_name_by_id(db, zodiac_id)
                degree_val = _parse_degree(degree_raw)
                degree_str = f"{degree_val:.3f}°" if degree_val is not None else None
                signs_summary.append(
                    {
                        "planet": planet_name,
                        "sign": (zodiac_name.lower() if zodiac_name else None),
                        "degree": degree_str,
                    }
                )
            else:
                signs_summary.append({"planet": planet_name, "sign": None, "degree": None})

        return JSONResponse(content={"signs": signs_summary})

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao recuperar signos por planeta: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao recuperar signos")
