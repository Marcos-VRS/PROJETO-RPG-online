"""Avança a sequência de auto-increment de CharacterSheetV2 para acima
de max(CharacterSheet.id) + 1000.

**Por quê:** V1 (CharacterSheet) e V2 (CharacterSheetV2) são tabelas
separadas, cada uma com seu próprio contador. Por padrão, ambas começam
em 1 e crescem em paralelo — então os IDs colidem (ex: V1 id=4 e V2 id=4
existem simultaneamente). A tela de jogo usa IDs pra identificar minis;
duas fichas com mesmo ID causam:
  - dois minis com mesmo data-character-id no DOM
  - rd6ApplySceneStateToBar marca ambos como current-turn
  - rd6CharById retorna o primeiro match, ignorando o outro

Solução: setar a sequence da V2 pra max(max(V1.id), max(V2.id)) + 1000.
Próximos V2 nascem em IDs altos (1100+) que nunca vão colidir com V1.

Idempotente: re-rodar não faz nada porque a sequence atual já será > target
(SQLite só aceita aumentar; o ON CONFLICT REPLACE força o valor).
"""
from django.db import migrations


def _bump_v2_sequence(apps, schema_editor):
    CharacterSheet = apps.get_model("gurps", "CharacterSheet")
    CharacterSheetV2 = apps.get_model("gurps", "CharacterSheetV2")

    max_v1 = (
        CharacterSheet.objects.order_by("-id").values_list("id", flat=True).first() or 0
    )
    max_v2 = (
        CharacterSheetV2.objects.order_by("-id").values_list("id", flat=True).first() or 0
    )
    target = max(max_v1, max_v2) + 1000

    conn = schema_editor.connection
    table = CharacterSheetV2._meta.db_table  # "gurps_charactersheetv2"

    with conn.cursor() as cur:
        if conn.vendor == "sqlite":
            # sqlite_sequence é populada na 1ª insert. Garantimos a entrada.
            cur.execute(
                "INSERT INTO sqlite_sequence (name, seq) "
                "SELECT ?, ? WHERE NOT EXISTS "
                "(SELECT 1 FROM sqlite_sequence WHERE name = ?)",
                [table, target, table],
            )
            cur.execute(
                "UPDATE sqlite_sequence SET seq = ? WHERE name = ? AND seq < ?",
                [target, table, target],
            )
        elif conn.vendor == "postgresql":
            cur.execute(
                "SELECT setval(pg_get_serial_sequence(%s, 'id'), %s, true)",
                [table, target],
            )
        # MySQL / outros bancos não suportados nesse projeto — ignora.


def _noop_reverse(apps, schema_editor):
    """Reverter não faz sentido (não dá pra "abaixar" a sequence sem perder ids)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("gurps", "0058_charactersheetv2_maneuvers_defense_and_more"),
    ]

    operations = [
        migrations.RunPython(_bump_v2_sequence, _noop_reverse),
    ]
