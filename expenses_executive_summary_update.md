# Actualización de Integración de Gastos en Resumen Ejecutivo (Backend -> Frontend)

Para: **Equipo Frontend (Flutter)**
De: **AI Backend Agent**
Fecha: **2026-06-07**
Estado: **Desplegado en Backend**

Se ha implementado el soporte para reportar egresos por gastos (totales y pagados) en los **Resúmenes Ejecutivos** (Executive Summaries) tanto a nivel **global** como **desglosado por sucursal**.

---

## 1. Cambios en la API y Modelos

Los nuevos campos se han integrado en dos niveles dentro de los endpoints de resúmenes ejecutivos (ej. `GET /executive-summaries` y `GET /executive-summaries/{id}`):

### A. Nivel Global (Raíz del Reporte)
Campos globales consolidados del periodo:
*   `expensesTotal` (entero, `int`): El monto total de todos los gastos activos registrados en el periodo del reporte de todas las sucursales (en **centavos**).
*   `expensesPaid` (entero, `int`): El monto total de los gastos activos pagados (`status == "paid"`) en el periodo de todas las sucursales (en **centavos**).

### B. Nivel de Sucursal (En la lista de sucursales)
Cada objeto sucursal dentro del arreglo `commercialBranches` ahora incluye sus respectivos gastos:
*   `commercialBranches[].expensesTotal` (entero, `int`): Gastos registrados para esta sucursal específica (en **centavos**).
*   `commercialBranches[].expensesPaid` (entero, `int`): Gastos pagados para esta sucursal específica (en **centavos**).

---

## 2. Ejemplo de Respuesta JSON Actualizada

```json
{
  "id": "647f8a7e9b1c2d3e4f5a6b7c",
  "dateId": "2026-06",
  "type": "monthly",
  "year": 2026,
  "month": 6,
  "startDate": 1780272000000,
  "endDate": 1782863999999,
  "salesTotal": 4500000,
  "creditSales": 1500000,
  "cashSales": 3000000,
  "salesTotalCost": 2500000,
  "totalInvoices": 150,
  "totalPendingInvoices": 1200000,
  "inventoryTotalCost": 9800000,
  "expensesTotal": 850000,  // <-- Consolidados Globales: $8,500.00
  "expensesPaid": 500000,   // <-- Consolidados Globales: $5,000.00
  "commercialBranches": [
    {
      "branchId": "branch_nic_1",
      "total": 3000000,
      "totalCost": 1800000,
      "totalPaid": 2000000,
      "totalOwed": 1000000,
      "expensesTotal": 600000, // <-- NUEVO: Gastos en Sucursal: $6,000.00
      "expensesPaid": 400000   // <-- NUEVO: Gastos Pagados en Sucursal: $4,000.00
      // ... otros campos de sucursal ...
    },
    {
      "branchId": "branch_nic_2",
      "total": 1500000,
      "totalCost": 700000,
      "totalPaid": 1000000,
      "totalOwed": 500000,
      "expensesTotal": 250000, // <-- NUEVO: Gastos en Sucursal: $2,500.00
      "expensesPaid": 100000   // <-- NUEVO: Gastos Pagados en Sucursal: $1,000.00
      // ... otros campos de sucursal ...
    }
  ],
  ...
}
```

---

## 3. Acciones requeridas en Flutter

### Paso A: Actualizar el Modelo `CommercialBranchDetail`
Añade las propiedades y el parseo en la clase modelo de las sucursales:

```dart
class CommercialBranchDetail {
  // ... propiedades existentes ...
  final int expensesTotal;
  final int expensesPaid;

  CommercialBranchDetail({
    // ... otros campos ...
    this.expensesTotal = 0,
    this.expensesPaid = 0,
  });

  factory CommercialBranchDetail.fromJson(Map<String, dynamic> json) {
    return CommercialBranchDetail(
      // ... otros mapeos ...
      expensesTotal: json['expensesTotal'] ?? 0,
      expensesPaid: json['expensesPaid'] ?? 0,
    );
  }

  // Deuda calculada para la sucursal
  int get expensesOwed => expensesTotal - expensesPaid;
}
```

### Paso B: Actualizar el Modelo `ExecutiveSummary`
Añade las propiedades globales y mapeo `fromJson`:

```dart
class ExecutiveSummary {
  // ... propiedades existentes ...
  final int expensesTotal;
  final int expensesPaid;
  final List<CommercialBranchDetail> commercialBranches;

  ExecutiveSummary({
    // ... otros campos ...
    this.expensesTotal = 0,
    this.expensesPaid = 0,
    required this.commercialBranches,
  });

  factory ExecutiveSummary.fromJson(Map<String, dynamic> json) {
    return ExecutiveSummary(
      // ... otros mapeos ...
      expensesTotal: json['expensesTotal'] ?? 0,
      expensesPaid: json['expensesPaid'] ?? 0,
      commercialBranches: (json['commercialBranches'] as List)
          .map((e) => CommercialBranchDetail.fromJson(e))
          .toList(),
    );
  }

  // Deuda consolidada global
  int get expensesOwed => expensesTotal - expensesPaid;
}
```

### Paso C: Actualizar la UI del Reporte Ejecutivo
1.  **En la cabecera / resumen global**: Muestra los totales consolidados (`summary.expensesTotal` y `summary.expensesPaid`).
2.  **En la tabla / desglose de sucursales**: Añade columnas o filas para reflejar cuánto gastó y pagó cada sucursal en particular (`branch.expensesTotal`, `branch.expensesPaid` y el pendiente calculado `branch.expensesOwed`).
3.  **Conversión de Moneda**: Recuerda formatear dividiendo el entero entre `100.0` para convertir los centavos a decimales.
