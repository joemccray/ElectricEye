# Traceability Matrix

This document provides a traceability matrix for the ElectricEye Django project, mapping database tables to models, serializers, viewsets, and API URLs.

| DB Table      | Model   | Serializer        | ViewSet         | URL Example      |
|---------------|---------|-------------------|-----------------|------------------|
| `scans_scan`  | `Scan`  | `ScanSerializer`  | `ScanViewSet`   | `/api/scans/`    |
| `scans_finding`| `Finding`| `FindingSerializer`| `FindingViewSet`  | `/api/findings/` |
