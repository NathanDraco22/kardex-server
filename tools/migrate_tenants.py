"""CLI del runner de migraciones por tenant.

Uso desde la raiz de ``kardex-server``:

    python tools/migrate_tenants.py --dry-run
    python tools/migrate_tenants.py --indexes --tenant tiendaA
    python tools/migrate_tenants.py --adopt --dry-run

La implementacion vive en ``kardex.core.tenant.migrate_tenants``.
"""

import sys

from kardex.core.tenant.migrate_tenants import main


if __name__ == "__main__":
    sys.exit(main())
