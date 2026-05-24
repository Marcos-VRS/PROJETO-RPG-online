# Conversões de Unidades — roll3d6 RPG

> **Política do projeto:** GURPS publicou em imperial; o roll3d6 exibe **métrico/brasileiro**.
> **Regra de ouro:** o que estiver em `gurps/data/*.json` permanece como no livro (referência rastreável); a conversão acontece **só no momento de exibir** ao usuário.

---

## 1. A simplificação polêmica

**1 yard = 1 metro** no roll3d6.

Yard real = 0,9144 m. A diferença é ~9%. Por que ignorar?
- GURPS é granular em hexes (1 hex = 1 yard). Em um mapa de jogo, "1 hex = 1 m" é mais intuitivo pro jogador brasileiro.
- Range de armas, distância de magia, área de efeito — tudo em yards no livro. Converter pra metros com 0,914× geraria valores quebrados ("9,14 m" é horrível na UI).
- A inexatidão é homogênea (afeta tudo igualmente), então o balanço do sistema fica preservado.

**Implicação prática:** sempre que o livro diz "5 yards", a UI mostra "5 m". Não há conversão real; é renomeação.

---

## 2. Tabela completa

| GURPS | roll3d6 | Fator | Onde aparece |
|---|---|---|---|
| **yard** | **m** | 1:1 | Range, Reach, Basic Move, distância em geral |
| **hex** | **m** (no grid) | 1 hex = 1 m | Mapa, movimento |
| **inch** | **cm** | × 2,54 | Altura de personagem, escala de objetos |
| **foot** | **cm** | × 30,48 | Tamanho de objetos médios; ou **m** se ≥1m |
| **mile** | **km** | × 1,609 | Distância overland |
| **lb (libra)** | **kg** | × 0,4536 | Peso de equipamento, BL, encumbrance |
| **oz (onça)** | **g** | × 28,35 | Pequenos pesos |
| **gallon (US)** | **L** | × 3,785 | Líquidos |
| **°F** | **°C** | (F−32) × 5/9 | Temperatura |
| **psi** | **kPa** | × 6,895 | Pressão (raro) |

---

## 3. Arredondamento

- **Distâncias** (yard/hex → m): 1:1 sem arredondamento (já é inteiro).
- **Peso** (lb → kg): 1 casa decimal. Ex: 20 lb → 9,1 kg.
- **Peso pequeno** (oz → g): inteiro. Ex: 4 oz → 113 g.
- **Altura/tamanho** (in/ft → cm): inteiro. Ex: 6 ft → 183 cm.
- **Temperatura**: inteiro.

---

## 4. Helper Python

A criar em `gurps/units.py`:

```python
"""Conversões de unidades GURPS (imperial) → métrico (roll3d6 default)."""

LB_TO_KG = 0.4536
OZ_TO_G = 28.35
IN_TO_CM = 2.54
FT_TO_CM = 30.48
MI_TO_KM = 1.609

def lb_to_kg(lb: float, decimals: int = 1) -> float:
    return round(lb * LB_TO_KG, decimals)

def oz_to_g(oz: float) -> int:
    return round(oz * OZ_TO_G)

def in_to_cm(inches: float) -> int:
    return round(inches * IN_TO_CM)

def ft_to_cm(ft: float) -> int:
    return round(ft * FT_TO_CM)

def yards_to_m(yd: float) -> float:
    """Conversão 1:1 por convenção do projeto. Função existe pra alinhamento semântico."""
    return float(yd)

def fmt_weight_kg(lb: float) -> str:
    """Retorna 'X kg' ou 'X g' conforme escala."""
    g = lb * 453.6
    if g < 1000:
        return f"{round(g)} g"
    return f"{round(g / 1000, 1)} kg"
```

## 5. Helper JS

A criar em `base_static/global/js/util/units.js`:

```javascript
// Conversões GURPS (imperial) → métrico (roll3d6).
window.rd6Units = {
  lbToKg: (lb) => Math.round(lb * 4.536) / 10,
  ozToG:  (oz) => Math.round(oz * 28.35),
  inToCm: (inches) => Math.round(inches * 2.54),
  ftToCm: (ft) => Math.round(ft * 30.48),
  yardsToM: (yd) => yd,
  fmtWeight: (lb) => {
    const g = lb * 453.6;
    return g < 1000 ? `${Math.round(g)} g` : `${(Math.round(g / 100) / 10).toFixed(1)} kg`;
  },
};
```

---

## 6. Migration de dados existentes

Não precisa. Os JSONs do catálogo **continuam em imperial** porque servem de referência ao livro. Conversão é só na exibição.

Exceções (campos onde já pode ser métrico):
- `runtime_stats.hp_atual` / `fp_atual` → inteiros, sem unidade.
- `secondary_modifiers.basic_move` → inteiro, "m/s".
- Distâncias custom desenhadas no mapa → sempre **metros**.
