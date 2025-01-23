============================
Personalizaciones de cliente
============================

.. |badge1| image:: /custom_pnt/static/img/status.png
    :alt: Production/Stable
.. |badge2| image:: /custom_pnt/static/img/license.png
    :alt: License: LGPL-3

|badge1| |badge2|

Personalizaciones solicitadas o necesarias para el funcionamiento del cliente.

**Índice de contenidos**

.. contents::
   :local:

Instalación
===========

Acceder a aplicaciones e instalar el módulo *Personalizaciones del cliente*
(custom_pnt).

Configuración
=============
* Residuos
 - Tabla LER para residuos, LER con 6 dígitos normales, con 8 dígitos RAEE, con * en último dígito peligrosos. Hay que indicar el código como corresponde los checks de peligrosidaad y RAEE se marca automáticamente.
 - Las tablas de la pestaña residuo dentro de un residuo indica las tablas estandar del mismo.
* Tercero
 - Los choferes solo se pueden definir como contacto de un tercero.
 - Los código NIMA se indican por tercero si son compañía o dirección de entrega. Un tecero puede tener varios NIMAS según su tipo, cada NIMA puede tener muchos códigos de autorización y cada código de autorización puede tener diferentes LER.
* Contratos
 - Los contratos son las entidades que se utilizarán par la gestión de los documentos únicos DU.
 - Los contratos pueden tener contratos padre que ampliarán productos o servicios del contrato principal prevaleciendo primero siempre productos o servicios del contrato hijo.

Uso
===

Funcionamiento normal de odoo.

Limitaciones / Problemas conocidos
==================================

Ninguna conocida.

Registro de cambios
===================

14.0.1.0.5 (04-05-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Se añade gestión de contratos.

14.0.1.0.4 (28-03-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Se añade campos para la gestión de residuos códigos LER, NIMA y códigos de autorización.
* Se añade la gestión de tablas por residuo y tercero.

14.0.1.0.3 (22-03-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Se añade campos para la gestión de residuos y categorías MARPOL.

14.0.1.0.2 (16-03-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Se añade funcionalidad para la gestión de categorías de flota.

14.0.1.0.1 (13-03-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Se añade funcionalidad para la gestión, alertas y en servicios en flota.
* Se añade funcionalidad para la gestión, alertas en chofer.
* Gestión tarjetas de transporte y Clase de permisos de circulación.

14.0.1.0.0 (11-03-2022)
~~~~~~~~~~~~~~~~~~~~~~~

* Versión inicial.

Creditos
========

Autores
~~~~~~~

* `Punt Sistemes <https://www.puntsistemes.es>`__

Contribuidores
~~~~~~~~~~~~~~

* `Punt Sistemes <https://www.puntsistemes.es>`__:

  * Rafa Martínez <rmartinez@puntsistemes.es>
  * Tolo Torres <ttorres@puntsistemes.es>
  * Pedro Montagud <pmontagud@puntsistemes.es>

Mantenedores
~~~~~~~~~~~~

Mantenido por `Punt Sistemes <https://www.puntsistemes.es>`__.

.. image:: /custom_pnt/static/img/punt-sistemes.png
   :alt: Punt Sistemes
   :target: https://www.puntsistemes.es
