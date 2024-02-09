# Sundash dev notes


### Release plan

  * [0.0.7]  User sessions (upgrade of core design to handle event coro lifetime)
  * [0.0.8]  App routing (URLs, in-app switches)
  * [0.0.9]  Variables (initialization, realtime update, pretty interface)

  *          Documentation
  *          Theme customization and Tochka theme

  * [0.1.0]  Staging-ready release

  * [0.2.0]  Tables
      * Form inputs in tables
      * Table pagination and actions
      * Autobuild of tables (pydantic, django)
      * Nested schema in tables

  * [0.3.0]  Auth
      * Auth handling in app
      * oauth2 integration & token storage


**app**

  * scheduler
  * define sundash extension modules basics (`sundash.ext._base`)
  * live update (watchdog)
  * find the format for communication description (need to draw...)

**frontend**

  * theme customization:

      Tochka design resources: https://tochka.com/rko/design/
  
      https://dev.to/ananyaneogi/create-a-dark-light-mode-switch-with-css-variables-34l8

  * adaptive layout out-of-box


### ext candidates

  * tochka-auth
  * vega
  * three-js
  * tables
  * admin
  * sqlite
  * asyncpg
  * pydantic
  * docs-maker


### ideas

  * libs for classic admin panels (django replacement)
  * custom dashboards (grafana replacement)
  * trading monitoring tools (realtime portfolio management, control panel, etc...)
  * abstract platform for interactive data management
  * full-loaded trading terminals
  * custom data visualization
  * advanced admin (with building nested structure schema into table)
  * user shared sessions (minimal working chat)
  * 3d graphics
