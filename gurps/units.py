"""Conversões de unidades GURPS (imperial) → métrico (default do roll3d6).

Política do projeto: GURPS publica em imperial; a UI do roll3d6 mostra em
métrico/brasileiro. Conversão acontece SÓ no momento de exibir; JSONs do
catálogo (gurps/data/*.json) permanecem em imperial pra rastreabilidade
ao livro.

Regra de ouro: **1 yard = 1 metro** (simplificação intencional do user;
yard real = 0.9144 m, mas a diferença é homogênea e não afeta balanço).

Detalhes em docs/UNIT_CONVERSIONS.md.
"""

LB_TO_KG = 0.4536
OZ_TO_G = 28.35
IN_TO_CM = 2.54
FT_TO_CM = 30.48
MI_TO_KM = 1.609


def lb_to_kg(lb: float, decimals: int = 1) -> float:
    """20 lb → 9.1 kg."""
    return round(lb * LB_TO_KG, decimals)


def oz_to_g(oz: float) -> int:
    """4 oz → 113 g."""
    return round(oz * OZ_TO_G)


def in_to_cm(inches: float) -> int:
    """72 in → 183 cm."""
    return round(inches * IN_TO_CM)


def ft_to_cm(ft: float) -> int:
    """6 ft → 183 cm."""
    return round(ft * FT_TO_CM)


def yards_to_m(yd: float) -> float:
    """Conversão 1:1 por convenção do projeto. Função existe pra
    alinhamento semântico ao chamar."""
    return float(yd)


def fmt_weight(lb: float) -> str:
    """Retorna 'X kg' ou 'X g' conforme escala. Ex: 0.5 lb → '227 g'."""
    g = lb * 453.6
    if g < 1000:
        return f"{round(g)} g"
    return f"{round(g / 1000, 1)} kg"
