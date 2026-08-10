# -*- coding: utf-8 -*-
"""Backfill opaque QR verification tokens for existing quality checks."""

import secrets


def migrate(cr, version):
    cr.execute(
        "SELECT id FROM amunet_quality_check "
        "WHERE public_verify_token IS NULL OR public_verify_token = ''"
    )
    for (check_id,) in cr.fetchall():
        cr.execute(
            "UPDATE amunet_quality_check SET public_verify_token = %s WHERE id = %s",
            [secrets.token_urlsafe(32), check_id],
        )
