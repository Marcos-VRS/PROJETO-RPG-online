// Conversões GURPS (imperial) → métrico (default roll3d6).
// Política: 1 yard = 1 metro (simplificação intencional). Ver docs/UNIT_CONVERSIONS.md.
window.rd6Units = {
    LB_TO_KG: 0.4536,
    OZ_TO_G: 28.35,
    IN_TO_CM: 2.54,
    FT_TO_CM: 30.48,

    lbToKg: function (lb, decimals) {
        decimals = decimals == null ? 1 : decimals;
        var f = Math.pow(10, decimals);
        return Math.round(lb * 0.4536 * f) / f;
    },
    ozToG: function (oz) { return Math.round(oz * 28.35); },
    inToCm: function (inches) { return Math.round(inches * 2.54); },
    ftToCm: function (ft) { return Math.round(ft * 30.48); },
    yardsToM: function (yd) { return yd; },

    // Format "X kg" ou "X g" conforme escala
    fmtWeight: function (lb) {
        var g = lb * 453.6;
        if (g < 1000) return Math.round(g) + ' g';
        return (Math.round(g / 100) / 10).toFixed(1) + ' kg';
    },
};
