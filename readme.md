# ERP Modular para la Gestión Integral de Negocios

Este proyecto es un sistema **ERP modular** desarrollado desde cero con **FastAPI y PostgreSQL**, orientado a resolver problemas reales de **logística, administración, stock, transporte y ventas**. Diseñado con un enfoque práctico y escalable, busca facilitar la organización interna de pequeñas y medianas empresas.

---

## 🚀 Objetivo del Proyecto

El objetivo principal es construir un ERP adaptable que permita a cualquier negocio:

- Controlar stock y almacenes
- Administrar compras y ventas
- Coordinar logística y transporte
- Gestionar usuarios, clientes y empleados
- Unificar operaciones en un solo sistema

El sistema incorpora un **módulo de ecommerce**, pero su enfoque no es ser una tienda online aislada, sino una solución integral que conecte ventas con la operación real del negocio.

---

## 🧩 Módulos del ERP

El sistema se estructura en módulos independientes, permitiendo activarlos o integrarlos según las necesidades del negocio.

### Módulos actuales o en desarrollo:

1. **Usuarios y Autenticación**
   - Registro, login, recuperación de contraseña
   - Verificación por email
   - Doble factor (OTP)
   - Roles de usuario (admin, operador, cliente)

2. **Gestión de Productos y Stock**
   - CRUD de productos y categorías
   - Control de stock por depósito

3. **Compras y Ventas**
   - Carrito de compras
   - Generación de órdenes
   - Módulo de ecommerce opcional

4. **Logística y Transporte**
   - Gestión de envíos y entregas
   - Asignación de transporte
   - Estados de entrega

5. **Panel de Administración**
   - Gestión de usuarios, permisos y datos
   - Dashboard con métricas clave

6. **Notificaciones y Mensajes**
   - Envío de correos (activación, recuperación, avisos)
   - Mensajería interna (cliente ↔ administración)

7. **Seguridad**
   - Tokens JWT y verificación de acceso
   - Logs de actividad
   - Manejo de intentos fallidos

---

## 🧠 Tecnologías utilizadas

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Base de datos:** PostgreSQL
- **Frontend:** Jinja2 + HTML + Bootstrap (modular)
- **Seguridad:** JWT, autenticación 2FA por OTP
- **Emails:** SMTP + plantillas personalizadas
- **Deploy:** Docker, VPS

---

## 🔐 Roles implementados

El sistema soporta múltiples niveles de acceso:

- **Administrador**: control total del sistema
- **Empleado / Operador**: gestión de stock, ventas, pedidos o logística según permisos
- **Cliente**: compra, seguimiento de pedidos y gestión de perfil

---

## 🛣️ Roadmap (Próximos pasos)

- Módulo de reportes PDF / Excel
- API externa para integraciones (tiendas, logística)
- Gestión de cuentas corrientes y facturación
- Notificaciones push o WhatsApp
- Multi-empresa / multi-sucursal
- Interfaz más avanzada para el panel administrativo

---

## 👨‍💻 Autor

**José Aníbal Modad** – Desarrollador backend autodidacta

- GitHub: [@turkomodad](https://github.com/turkomodad)
- LinkedIn: [jose-anibal-modad](https://www.linkedin.com/in/jose-anibal-modad)

---

## ⚙️ Estado del proyecto

> En desarrollo activo. Proyecto autodidacta para fines profesionales, con potencial de convertirse en una herramienta real para PYMEs del entorno logístico y comercial.
