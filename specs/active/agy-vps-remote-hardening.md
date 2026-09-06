# Spec: Enrutado de Comandos por `run_command` — Poda Local y Capa Remota VPS

## 1. Objetivo y Contexto

La capa de intervención remota de AGY **existe y funciona, pero está desconectada**. Los cinco
ejecutores remotos (`vps_exec`, `vps_reader`, `vps_patcher`, `vps_symbol_sync`, `vps_health`)
están versionados y despachados en `agy_cli.py:57-61`, pero **nada enruta hacia ellos**: el
2026-09-06 se registraron 18 invocaciones `ssh vps` crudas en `~/.agents/gate_audit.log` y
**cero** vía `agy-opt vps-run`. Salidas masivas (`mysqldump`, `SELECT JSON_ARRAYAGG(...)`)
entraron enteras a la ventana de contexto sin pasar por el podador.

### Hechos verificados en el relevamiento (no re-verificar)

| Hecho | Evidencia |
|---|---|
| El `overwrite` de hooks `PreToolUse` **sí** funciona en Antigravity | Correlación de 2 s entre comando crudo logueado por el blocker (`16:16:46`) y el evento `TERMINAL_PRUNE` (`16:16:48`) |
| El blocker loguea el comando **crudo** porque corre antes que el compresor | Orden de entradas en `~/.gemini/config/hooks.json` |
| `DIFF_COMPRESS = 1` no indica hook roto | `compress_diff.py:36` sólo registra si `reduction_ratio > 0.05`; un diff de código sin lockfiles no reduce |
| El interceptor no conoce `ssh` | `gate_diff_compressor_interceptor.py` sólo matchea `git diff`, `npm`, `pip`, `composer`, `pytest` |
| La regla de comandos ruidosos aborta ante pipes | `and "|" not in cmd`, y casi todo `ssh` no trivial lleva pipe |
| `vps` y `vps4` son la **misma máquina** dual-stack | `~/.ssh/config`: IPv6 `2800:6c0:5::1fbf` / IPv4 `168.181.184.103`, ambos puerto 5932, user root |
| Los patrones críticos alcanzan a `ssh` por substring, no por diseño | `CRITICAL_COMMAND_PATTERNS` hace `re.search` sobre la `CommandLine` completa |
| El enum real de `decision` tiene **5** valores, no 3 | Esquema embebido en el binario: `enum=allow,enum=deny,enum=ask,enum=force_ask,enum=deny_unless_prior_grant` |
| `ask` respeta la caché "Always Allow"; `force_ask` la ignora | Doc del contrato `PreToolUse` embebida en el binario |
| `overwrite` es merge **shallow de primer nivel**; la llamada modificada es la que ejecuta y queda registrada | Doc del contrato `PreToolUse` |
| Existe `permissionOverrides` (array): otorga permisos temporales desde el hook | Doc del contrato + `hooks_go_proto.(*PreToolHookResult).GetPermissionOverrides` |
| Varios handlers que matchean el mismo tool se agregan; no gana el primero | Empírico: blocker (`allow` + auditoría) y compresor (`overwrite`) actuaron ambos sobre la misma `run_command` |
| El cwd de todo hook es el directorio que contiene `hooks.json` | Doc "Hook Handler Fields"; hoy sería `~/.gemini/config/` |
| El `timeout` por defecto de un handler es 30 s; los hooks vigentes usan 5 s | Doc "Hook Handler Fields" + `~/.gemini/config/hooks.json` |
| `PostToolUse` debe emitir `{}`; existen además `PostInvocation` y `Stop`, hoy sin usar | Doc "Supported Event Types" |
| Los hooks **workspace-local** (`<workspace>/.agents/hooks.json`) **no cargaron** en print mode desde una carpeta no confiada; sólo cargó el compartido | Sonda ejecutada en esta sesión: el blocker global auditó el comando a las `18:20:42`, la sonda local nunca se emitió |
| **`--dangerously-skip-permissions` auto-aprueba también un `force_ask` emitido por un hook** | Sonda en el `hooks.json` compartido, corrida interactiva 2026-09-06 `18:31:56`: el hook emitió `force_ask`, no apareció prompt y el comando se ejecutó igual |
| El estándar global vive en `~/.gemini/config/rules/` (7 reglas `always_on`), **no** en `~/AGENTS.md` (que no existe) | `ls` del directorio + frontmatter de cada regla; `rules/` es el mecanismo documentado en el binario |
| Las reglas ya reflejan el flujo real: **0 menciones a OpenCode**; `sdd_gate.md:14` fija `Claude Code planifica ──► AGY construye` | `grep -i opencode ~/.gemini/config/rules/` sin resultados |
| Los hooks quedaron desfasados respecto de las reglas: 5 cadenas derivan a OpenCode | `gate_build_blocker.py:133,184,195,202` y `gate_pre_invocation.py:32` |
| El usuario **no usa OpenCode**; si lo usara sería sólo con la API de DeepSeek | Indicado por el usuario en esta sesión |

### Gap estructural

Los adaptadores están versionados y testeados (`src/adapters/`, 12 archivos en `tests/`), pero
**el pegamento de hooks no**: `gate_build_blocker.py`, `gate_diff_compressor_interceptor.py`,
`gate_ast_pruner_interceptor.py`, `gate_pre_invocation.py`, `gate_post_edit_healer.py`,
`gate_spec_auditor.py` y `agy_mode.py` viven sueltos en `~/.agents/hooks/`, y
`~/.gemini/config/hooks.json` en `~/.gemini/`. Ninguno está en el repo, ninguno tiene test.
`tests/test_diff_interceptor.py` testea `RegexDiffCompressor` (el adaptador), **no** el hook.
La capa donde vive la decisión de enrutado — exactamente la que falla — es la única sin cobertura.

### Alcance

### El agujero es uno solo, con dos caras

El podador AST vigila `view_file`. El agente también lee por `run_command`, y por ahí no hay
guardián — ni local ni remoto. Medido sobre `~/.agents/gate_audit.log`:

| Métrica | Valor |
|---|---|
| Llamadas `view_file` | 494 |
| Denegaciones del podador AST sobre esas 494 | **0** |
| Lecturas de código por `run_command` (`cat`/`head`/`sed -n` sobre `.py`, `.ts`, `.json`…) | 36 |
| Invocaciones `ssh` crudas | 18 |

Y en `~/.agents/token_savings.log`, sobre todo el historial:

| Evento | Veces | Tokens |
|---|---|---|
| `LINTER_FIX` | 103 | 51.500 ⚠️ estimados |
| `POLYGLOT_L1_VALID` | 20 | 6.000 ⚠️ estimados |
| `TERMINAL_PRUNE` | 10 | 3.301 |
| `DATA_SCHEMA` | 1 | 3.631 |
| `AST_PRUNE` | **1** | 738 |
| `DIFF_COMPRESS` | **1** | 640 |

Los dos primeros son constantes, no mediciones: `gate_post_edit_healer.py:50,62` escribe
`tokens_before=1500` y `tokens_before=500` fijos. **Ahorro realmente medido en todo el
historial: ~8.310 tokens**, y `AST_PRUNE`/`DIFF_COMPRESS` dispararon una sola vez cada uno,
en los smoke tests del 2026-09-06 a las 14:30 y 14:28.

Por eso este spec trata local y remoto con **un solo clasificador**: es el mismo defecto —
el podador mira una puerta y el agente entra por la otra— y arreglar sólo la cara remota
dejaría en pie la que más se usa.

**Incluye:** clasificación de comandos de `run_command` (local y remota), guardián de lecturas
de código por esa vía, enrutado de consultas remotas hacia el ejecutor podado, enrutado de
escrituras remotas hacia el parcheador, fallback IPv6→IPv4, gate estricto para mutaciones
remotas, directiva VPS en el `BUILD_DIRECTIVE`, y versionado de los hooks dentro del repo.

**Queda afuera explícitamente:**
- Reescribir comandos interactivos, binarios (`mysqldump`, `tar`, `gzip`, `base64`) o de larga
  duración. Pasan crudos por decisión del usuario.
- Ejecutar el Gauntlet en remoto.
- Indexado remoto automático (`vps-index` sigue siendo manual).
- Instrumentar `gate_post_edit_healer.py` con tokens medidos en lugar de constantes.
  (Los tres últimos, detallados en «Trabajo posterior».)
- Tocar la configuración de OpenCode: el usuario no lo usa. Su `~/.config/opencode/config.json`
  es config muerta (claves `openai_base_url`/`api_base`/`auto-cascade` inexistentes en el esquema)
  y el router en el puerto 8080 nunca corrió. Fuera de alcance por irrelevante, no por riesgoso.
- Reescribir las 7 reglas de `~/.gemini/config/rules/`: ya están alineadas con el flujo real.

## 2. Dominio y Puertos

Nuevas entidades en `src/domain/ports.py`. Cero dependencias externas, sólo `dataclasses`,
`enum` y `abc.ABC`.

```python
class CommandScope(Enum):
    """Dónde se ejecuta el comando de una `run_command`."""

    LOCAL = "local"
    REMOTO = "remoto"  # la línea invoca ssh contra un alias conocido


class CommandKind(Enum):
    """Clasificación de un comando visto por el hook PreToolUse."""

    LECTURA_CODIGO = "lectura_codigo"  # cat/head/sed -n sobre archivo de código: se deniega con guía
    CONSULTA = "consulta"  # lectura/diagnóstico: remoto se reescribe al ejecutor podado
    ESCRITURA = "escritura"  # edita un archivo de código in situ: remoto se deniega con guía
    MUTACION = "mutacion"  # altera estado del sistema: se deniega
    INTERACTIVO = "interactivo"  # sin comando o requiere TTY: pasa crudo
    EXENTO = "exento"  # binario o de larga duración: pasa crudo


@dataclass(frozen=True)
class RemoteHost:
    """Alias SSH con su fallback de familia de direcciones."""

    alias: str
    fallback_alias: str | None
    port: int
    user: str


@dataclass(frozen=True)
class CommandClassification:
    """Resultado del análisis de una CommandLine de run_command."""

    scope: CommandScope
    kind: CommandKind
    inner_command: str  # el comando efectivo; en remoto, lo que va tras el alias ssh
    target_path: str | None  # archivo involucrado en LECTURA_CODIGO / ESCRITURA
    host_alias: str | None  # None cuando scope es LOCAL
    reason: str


@dataclass(frozen=True)
class RemoteExecutionResult:
    """Resultado de ejecutar un comando remoto con poda de salida."""

    exit_code: int
    clean_output: str
    host_used: str
    timed_out: bool
    original_lines: int
    pruned_lines: int
    reduction_ratio: float


class ICommandClassifier(ABC):
    """Puerto para clasificar la CommandLine de un run_command, local o remota."""

    @abstractmethod
    def classify(self, command_line: str) -> CommandClassification | None:
        """Devuelve la clasificación, o None si no hay nada que hacer con la línea."""
        raise NotImplementedError


class ICodeFileInspector(ABC):
    """Puerto para decidir si un archivo local justifica poda, sin salir del presupuesto del hook."""

    @abstractmethod
    def excede_umbral(self, path: str, umbral_lineas: int = 100) -> bool:
        """True si el archivo existe, tiene extensión de código y supera el umbral de líneas."""
        raise NotImplementedError


class IRemoteExecutor(ABC):
    """Puerto para ejecución remota con fallback de host y poda de salida."""

    @abstractmethod
    def execute(self, command: str, host: RemoteHost, timeout_s: int = 60) -> RemoteExecutionResult:
        """Ejecuta en remoto; ante fallo de resolución del alias primario, reintenta con el fallback."""
        raise NotImplementedError
```

`ITerminalPruner` y `ITokenTelemetry` **ya existen** y deben reusarse por Inyección de
Dependencias. Prohibido reimplementar la poda: `vps_exec.py` hoy duplica la lógica inline con
una lista de keywords propia, en violación del reuso y del DIP que audita `agy-opt audit-dip`.

### Datos de clasificación (decisiones ya tomadas, no re-derivar)

**CONSULTA** — se reescribe. Verbo inicial del comando interno en:
`cat`, `ls`, `ll`, `head`, `tail`, `grep`, `rg`, `find`, `stat`, `wc`, `du`, `df`, `ps`, `free`,
`uptime`, `journalctl`, `dmesg`, `id`, `whoami`, `hostname`, `uname`, `env`, `date`;
más `systemctl status|is-active|is-enabled|list-units`, `docker ps|logs|inspect|images`,
`git status|log|diff|show`, y `mysql`/`psql` cuya sentencia matchee `^\s*(SELECT|SHOW|DESCRIBE|EXPLAIN)\b`.

**MUTACION** — requiere confirmación (§ gate estricto):
`systemctl stop|disable|restart|mask`, `docker rm|rmi|down|stop|kill|prune`, `ufw`,
`rm -rf` sobre `/etc`, `/opt`, `/var/www`, `/srv`, `/home`, y sentencias
`DELETE|DROP|TRUNCATE|UPDATE` sin cláusula `WHERE`.

**INTERACTIVO** — pasa crudo: `ssh <host>` sin comando, o con flag `-t`/`-tt`.

**EXENTO** — pasa crudo. Verbo en `mysqldump`, `pg_dump`, `tar`, `gzip`, `zip`, `base64`, `dd`,
`scp`, `rsync` (binarios), o en `apt`, `apt-get`, `dnf`, `docker build`, `npm ci`,
`npm install`, `pip install`, `make` (larga duración, exceden el timeout del ejecutor).

**LECTURA_CODIGO** — se deniega con guía. Verbo `cat`, `less`, `more`, `bat` (sin rango) sobre
un archivo con extensión de código o datos, **sin** redirección ni heredoc. Un `head -n N`,
`tail -n N` o `sed -n 'a,bp'` es lectura acotada: **no** cae acá, es `CONSULTA`.
- En `LOCAL` sólo aplica si `ICodeFileInspector.excede_umbral(path)` — mismo criterio de 100
  líneas que ya usa el guardián de `view_file`, para no cambiar la política, sólo cerrar la
  segunda puerta.
- En `REMOTO` aplica por extensión, sin umbral: el hook **no puede** contar líneas remotas sin
  tocar la red, y `vps-read --ast` es la respuesta correcta igual.

**ESCRITURA** — edita un archivo de código in situ. Verbo `sed -i`, o `cat`/`tee`/`python3 -`
con heredoc (`<<`) o redirección (`>`, `>>`) hacia un archivo con extensión de código o config.
- En `LOCAL` pasa crudo: es la forma normal de editar; el blocker ya cubre rutas protegidas.
- En `REMOTO` se deniega con guía hacia `agy-opt vps-patch`, que valida sintaxis antes de
  escribir. Una traducción automática de heredoc a `--target/--replacement` no es posible, así
  que el mensaje del `deny` es el mecanismo.

### Precedencia de evaluación

```
INTERACTIVO → EXENTO → ESCRITURA → MUTACION → LECTURA_CODIGO → CONSULTA → (default) crudo
```

`EXENTO` va antes que `ESCRITURA` para que `mysqldump > dump.sql` no se confunda con una
edición de código. `ESCRITURA` va antes que el resto para que un heredoc no se lea como
consulta.

**Regla transversal e inviolable:** una línea con redirección (`>`, `>>`, `| tee`) o heredoc
**nunca** se reescribe hacia el ejecutor podado. Interponer un podador corrompería el archivo
que se está escribiendo. Puede denegarse, nunca reenrutarse.

Ante ambigüedad, **no reescribir**: el default seguro es dejar pasar el comando tal cual.

### Matriz de acción (`scope` × `kind`)

| | LOCAL | REMOTO |
|---|---|---|
| `LECTURA_CODIGO` | `deny` → rango acotado o `prune_python_ast.py` | `deny` → `agy-opt vps-read <f> --ast` |
| `CONSULTA` | `allow` (las reglas de ruido ya existentes siguen aplicando) | `allow` + `overwrite` → `vps_exec.py` |
| `ESCRITURA` | `allow` | `deny` → `agy-opt vps-patch` |
| `MUTACION` | `allow` (el blocker ya cubre lo irreversible) | `deny` → ejecución manual |
| `INTERACTIVO` / `EXENTO` | `allow` | `allow`, sin `overwrite` |

## 3. Casos de Uso y DTOs

Siete casos de uso. Los cuatro primeros son lógica de aplicación testeable; los tres últimos
son pegamento de hooks, que sólo puede testearse una vez ejecutado CU-7.

| CU | Nombre | Ubicación | Depende de |
|---|---|---|---|
| CU-1 | Clasificar comando (local y remoto) | `src/application/clasificar_comando.py` | `ICommandClassifier`, `ICodeFileInspector` |
| CU-2 | Ejecutar comando remoto podado | `src/application/ejecutar_comando_remoto.py` | `IRemoteExecutor`, `ITerminalPruner`, `ITokenTelemetry` |
| CU-3 | Resolver host con fallback | `src/adapters/remote_executor.py` | `RemoteHost` |
| CU-4 | Enrutar desde el hook | `hooks/gate_diff_compressor_interceptor.py` | CU-1, CU-7 |
| CU-5 | Gate estricto de mutación remota | `hooks/gate_build_blocker.py` | CU-1, CU-7 |
| CU-6 | Guardián de lecturas de código por `run_command` | `hooks/gate_ast_pruner_interceptor.py` | CU-1, CU-7 |
| CU-7 | Versionar los hooks en el repo | `hooks/`, `config/`, `install.sh` | — |

DTOs de aplicación: los definidos en §2. Pydantic no se usa acá — la entrada de los hooks es
JSON por stdin ya validado por el contrato de Antigravity, y el dominio es puro `dataclass`.

### CU-1 · Clasificar comando (local y remoto)
`src/application/clasificar_comando.py`. Recibe la `CommandLine` del hook y devuelve
`CommandClassification`, o `None` si no hay nada que hacer con la línea.

1. Detecta si invoca `ssh` contra un alias conocido → `scope = REMOTO`, y extrae el comando
   interno respetando comillas (usar `shlex`, **no** regex sobre la línea cruda). Ignora
   `ssh github.com` y cualquier alias no listado.
2. Si no, `scope = LOCAL` y el comando interno es la línea completa.
3. Aplica la precedencia de §2 sobre el comando interno, idéntica en ambos scopes; sólo la
   **acción** resultante difiere (ver matriz `scope` × `kind`).

Para `scope = LOCAL` y `kind = LECTURA_CODIGO`, consulta `ICodeFileInspector` para aplicar el
umbral de 100 líneas. Para `REMOTO` no lo consulta: no hay archivo local que inspeccionar.

**Restricción dura:** la clasificación corre dentro del presupuesto de 5 s del hook y **no debe
tocar la red bajo ninguna circunstancia** — nada de resolver DNS, abrir sockets ni consultar el
host remoto. Es análisis puramente léxico sobre la `CommandLine`. La ejecución remota (con su
timeout propio) ocurre después, ya fuera del hook, en el comando reescrito.

### CU-2 · Ejecutar comando remoto podado
`src/application/ejecutar_comando_remoto.py`. Orquesta `IRemoteExecutor` + `ITerminalPruner` +
`ITokenTelemetry`. Registra un evento `event_type="VPS_EXEC_PRUNE"`, `tool_name="vps_exec"`
sólo si `reduction_ratio > 0.05`, replicando el umbral ya usado por `compress_diff.py:36`.
Preserva el `exit_code` remoto: la poda nunca debe enmascarar un fallo.

### CU-3 · Resolver host con fallback
`src/adapters/remote_executor.py`. `vps` es el alias primario (IPv6); ante error de resolución
o `Network is unreachable`, reintenta una sola vez con `vps4` (IPv4) y refleja el alias
efectivamente usado en `RemoteExecutionResult.host_used`. Un fallo de autenticación o un
exit code remoto distinto de cero **no** disparan fallback.

### CU-4 · Enrutar desde el hook
`gate_diff_compressor_interceptor.py` incorpora la clasificación **antes** de la regla de
comandos ruidosos, y esta última pasa a ignorar toda línea con `scope = REMOTO` — lo que además
elimina el bug actual de pasar `'ssh'` como perfil a `prune_terminal_output.py` en vez del
comando real.

Acciones, según la matriz de §2:
- `(REMOTO, CONSULTA)` → `{"decision": "allow", "overwrite": {"CommandLine": "<vps_exec…>"}}`.
  Es el **único** caso que produce `overwrite`.
- `(REMOTO, ESCRITURA)` → `deny`, con el comando y la invocación `agy-opt vps-patch` sugerida.
- Todo lo demás → `allow` sin `overwrite`; `LECTURA_CODIGO` la resuelve CU-6 y `MUTACION` CU-5.

Además, quitar de la regla de comandos ruidosos la condición `"|" not in cmd`, que hoy la
inhabilita ante cualquier pipe — que es lo habitual en un comando no trivial.

### CU-5 · Gate estricto de mutación remota
`gate_build_blocker.py` incorpora `handle_remote_mutation(args)`, invocado desde
`handle_critical_only` para que actúe **también en modo build**. Devuelve `deny` con un motivo
que nombra el comando y ofrece la alternativa manual.

**Decisión cerrada por verificación empírica: usar `decision: "deny"`. Sin alternativa.**

El contrato admite cinco valores, y los cuatro que negocian permisos quedan descartados para este
caso de uso:

| Valor | Por qué no sirve acá |
|---|---|
| `allow` | No gatea nada. |
| `ask` | Respeta la caché "Always Allow": una mutación aprobada una vez no vuelve a preguntar nunca. |
| `force_ask` | **Verificado el 2026-09-06 a las 18:31:56: `--dangerously-skip-permissions` lo auto-aprueba en silencio.** El hook emitió `force_ask`, no apareció prompt y el comando se ejecutó. |
| `deny_unless_prior_grant` | Está en el enum pero no en la documentación; semántica sólo inferible del nombre. |

`deny` es bloqueo duro e inmediato, fuera del circuito de negociación de permisos: ninguna bandera
lo pisa. Como el usuario invoca AGY **siempre** con `--dangerously-skip-permissions`, cualquier
decisión que dependa de una confirmación interactiva es, en la práctica, un `allow`.

**Consecuencia de diseño:** el motivo del `deny` es la única interfaz que le queda al usuario, así
que debe ser instructivo, no un simple rechazo. Debe nombrar el comando bloqueado y ofrecer la vía
manual textual — el usuario ejecuta la mutación por su cuenta fuera del agente. Mismo criterio que
ya usa `handle_critical_only`: *"Si realmente lo necesitas, ejecútalo manualmente fuera del agente."*
> **Si resulta que lo auto-aprueba, degradar a `decision: "deny"`** con motivo instructivo — `deny`
> es bloqueo duro e inmediato, sin negociación de permisos, así que ninguna bandera lo pisa.
> Nunca degradar a `allow`.

### CU-6 · Guardián de lecturas de código por `run_command`
`gate_ast_pruner_interceptor.py` hoy sólo declara el matcher `view_file`. **Ésta es la causa
medida de que el podador AST haya denegado 0 de 494 lecturas**: el agente también lee con
`cat` por `run_command`, y por ahí no hay guardián.

Extender el hook a `run_command` (matcher nuevo en `config/hooks.json`, ver CU-7) y denegar
`kind = LECTURA_CODIGO`:
- `LOCAL` → mismo texto que el guardián de `view_file` ya usa, apuntando a un rango acotado o a
  `prune_python_ast.py`. Sólo cuando `ICodeFileInspector.excede_umbral(path)`.
- `REMOTO` → apuntando a `agy-opt vps-read <archivo> --ast`.

El hook de `view_file` queda tal cual: misma política, segunda puerta.

### CU-7 · Versionar los hooks y realinearlos con las reglas
Crear `hooks/` en la raíz del repo con los siete `gate_*.py` y `agy_mode.py`, más
`config/hooks.json` — que además incorpora el matcher `run_command` para
`gate_ast_pruner_interceptor.py` que exige CU-6 (hoy sólo está registrado para `view_file`). Extender `install.sh` para desplegarlos a `~/.agents/hooks/` y
`~/.gemini/config/hooks.json`, respetando el patrón de backup ya presente en `install.sh:32`.
Es requisito previo: sin esto, CU-4/5/6 se implementan sobre archivos que ningún test alcanza.

**Corrección incluida:** las 5 cadenas que derivan a OpenCode contradicen a `sdd_gate.md`, que
ya fija `Claude Code planifica ──► AGY construye`. Reescribirlas para que el modo plan derive al
modo build de AGY (`agy-mode build`), nunca a OpenCode:

| Archivo | Línea | Dice hoy |
|---|---|---|
| `gate_build_blocker.py` | 133 | "La implementación en código fuente debe realizarse en OpenCode…" |
| `gate_build_blocker.py` | 184 | "El versionado … debe realizarse en OpenCode." |
| `gate_build_blocker.py` | 195 | "Use OpenCode para /build." |
| `gate_build_blocker.py` | 202 | "…o OpenCode." |
| `gate_pre_invocation.py` | 32 | "4. DELEGACIÓN: Toda implementación de código se delega a OpenCode (/build)." |

**No tocar `install.sh:11` (`DEST_AGENTS_MD="$HOME/AGENTS.md"`) para "arreglar" el despliegue del
estándar.** `~/AGENTS.md` no existe a propósito: quedó superado por `~/.gemini/config/rules/`.
Desplegarlo duplicaría el estándar en dos lugares. Si algo hay que hacer con ese paso de
`install.sh`, es eliminarlo — pero eso queda fuera de este spec.

## 4. Matriz de Pruebas (RED Suite)

Convención del repo: tests planos bajo `tests/`, `unittest.TestCase`, importando desde `src.`.

| # | Escenario (Gherkin) | Archivo |
|---|---|---|
| 1 | Dado `ssh vps "journalctl -u api -n 500"`, cuando se clasifica, entonces `scope == REMOTO`, `kind == CONSULTA` e `inner_command == "journalctl -u api -n 500"` | `tests/test_command_classifier.py` |
| 2 | Dado `ssh vps` sin comando, entonces `kind == INTERACTIVO` y no se reescribe | `tests/test_command_classifier.py` |
| 3 | Dado `ssh vps "mysqldump --no-tablespaces db t > /tmp/d.sql"`, entonces `kind == EXENTO` por doble causa (binario y redirección) | `tests/test_command_classifier.py` |
| 4 | Dado `ssh vps "systemctl stop nginx"`, entonces `kind == MUTACION` | `tests/test_command_classifier.py` |
| 5 | Dado `ssh vps "mysql -e 'SELECT 1'"`, entonces `CONSULTA`; dado `"mysql -e 'DELETE FROM t'"` sin WHERE, entonces `MUTACION` | `tests/test_command_classifier.py` |
| 6 | Dado `ssh github.com`, entonces `classify` devuelve `None` (host fuera de alcance) | `tests/test_command_classifier.py` |
| 7 | Dado un comando con comillas anidadas escapadas, entonces el parseo con `shlex` extrae el comando interno sin corromperlo | `tests/test_command_classifier.py` |
| 8 | Dado que el alias primario falla por `Network is unreachable`, entonces se reintenta con `vps4` y `host_used == "vps4"` | `tests/test_remote_executor.py` |
| 9 | Dado un exit code remoto distinto de cero, entonces **no** hay fallback y el exit code se preserva tras la poda | `tests/test_remote_executor.py` |
| 10 | Dada una salida de 500 líneas, entonces se poda vía `ITerminalPruner` inyectado y se registra `VPS_EXEC_PRUNE` sólo si `reduction_ratio > 0.05` | `tests/test_remote_executor.py` |
| 11 | Dado un timeout, entonces `timed_out is True` y `exit_code == 124` | `tests/test_remote_executor.py` |
| 12 | Dado un payload de hook con `CONSULTA`, entonces la respuesta contiene `overwrite.CommandLine` apuntando al ejecutor remoto | `tests/test_remote_interceptor.py` |
| 13 | Dado un payload con `MUTACION`, entonces `decision == "deny"` y el motivo nombra el comando bloqueado y ofrece la vía manual | `tests/test_remote_interceptor.py` |
| 14 | Dado un payload con `EXENTO` o `INTERACTIVO`, entonces la respuesta es `allow` **sin** `overwrite` | `tests/test_remote_interceptor.py` |
| 15 | Dado `ssh vps "pytest"`, entonces la regla de comandos ruidosos no se aplica y no se pasa `'ssh'` como perfil | `tests/test_remote_interceptor.py` |
| 16 | Dado `ssh vps "cat /srv/app/main.py"`, entonces el guardián AST deniega y sugiere `vps-read --ast` | `tests/test_remote_interceptor.py` |
| 17 | Dado cualquier payload de mutación remota, entonces la decisión **nunca** es `allow`, `ask` ni `force_ask` — los tres son auto-aprobables bajo `--dangerously-skip-permissions` | `tests/test_remote_interceptor.py` |
| 18 | Dado el árbol `hooks/` versionado, entonces ningún `gate_*.py` contiene la cadena "OpenCode" | `tests/test_hooks_alineados.py` |
| 19 | Dado `cat src/main.py` local con 400 líneas, entonces `(LOCAL, LECTURA_CODIGO)` y el hook deniega citando el umbral | `tests/test_command_classifier.py` |
| 20 | Dado `cat src/main.py` local con 40 líneas, entonces **no** se deniega: no supera el umbral de 100 | `tests/test_command_classifier.py` |
| 21 | Dado `head -n 65 src/main.py`, entonces `CONSULTA` y no se deniega: es lectura acotada | `tests/test_command_classifier.py` |
| 22 | Dado `ssh vps "cat /srv/app/main.py"`, entonces `(REMOTO, LECTURA_CODIGO)` sin consultar `ICodeFileInspector` | `tests/test_command_classifier.py` |
| 23 | Dado `cat << 'EOF' > scripts/gen.py …`, entonces `ESCRITURA`, **no** `LECTURA_CODIGO`, y en LOCAL pasa con `allow` | `tests/test_command_classifier.py` |
| 24 | Dado `ssh vps "sed -i 's/a/b/' /srv/app.py"`, entonces `(REMOTO, ESCRITURA)` y el hook deniega sugiriendo `agy-opt vps-patch` | `tests/test_remote_interceptor.py` |
| 25 | Dado `ssh vps "mysqldump db > /tmp/d.sql"`, entonces `EXENTO` — `EXENTO` precede a `ESCRITURA` | `tests/test_command_classifier.py` |
| 26 | Dada cualquier línea con `>`, `>>`, `\| tee` o heredoc, entonces la respuesta **nunca** trae `overwrite` | `tests/test_remote_interceptor.py` |
| 27 | Dado `ICodeFileInspector` con un path inexistente, entonces `excede_umbral` devuelve `False` sin lanzar | `tests/test_code_file_inspector.py` |

## 5. Criterios del Gauntlet

```bash
cd /home/agustin/proyectos_software/agy-token-optimizer
ruff check . && ruff format --check .
pyright
agy-opt audit-dip
pytest --cov=src --cov-fail-under=85
python3 -m pytest tests/test_command_classifier.py tests/test_remote_executor.py \
  tests/test_remote_interceptor.py tests/test_code_file_inspector.py tests/test_hooks_alineados.py -v
```

Verificación funcional de extremo a extremo, posterior al Gauntlet:

```bash
./install.sh
agy-opt vps-health
agy-opt vps-run "journalctl -n 200 --no-pager"
grep -c "VPS_EXEC_PRUNE" ~/.agents/token_savings.log   # debe ser > 0
```

Criterios de aceptación:
- Cobertura ≥ 85 % sobre `src/`.
- 0 diagnósticos de `pyright` en modo strict, 0 hallazgos de `ruff`.
- 0 violaciones DIP: `vps_exec.py` no reimplementa poda; consume `ITerminalPruner` inyectado.
- Todo `__init__.py` de 0 bytes.
- Ningún `import logging` en `src/adapters/` ni `src/domain/`.
- Tras el despliegue, una sesión real de AGY contra el VPS registra al menos un evento
  `VPS_EXEC_PRUNE` y cero invocaciones `ssh` crudas de tipo CONSULTA en `gate_audit.log`.
- **Métrica de cierre del agujero local:** tras una sesión normal de trabajo local, el conteo de
  `AST_PRUNE` en `token_savings.log` deja de ser 1. Es la única prueba de que el guardián dejó de
  mirar una sola puerta:

```bash
grep -c '"event_type": "AST_PRUNE"' ~/.agents/token_savings.log
grep 'tool="run_command"' ~/.agents/gate_audit.log | grep -c 'decision="deny"'
```

### Orden de ejecución sugerido

1. **CU-7** — versionar los hooks y realinearlos. Va primero porque los tests 12-27 no pueden
   existir mientras los hooks estén fuera del repo.
2. **CU-1 + CU-3** — dominio y adaptadores (tests 1-11, 19-23, 25, 27).
3. **CU-2** — ejecución podada reusando `ITerminalPruner`.
4. **CU-6 primero entre los hooks**, luego CU-4 y CU-5 (tests 12-18, 24, 26).
   CU-6 antes que los demás porque cierra el agujero local, que es el de mayor retorno medido y
   no depende del VPS: si el trabajo se interrumpe, lo ya hecho igual rinde.
5. Despliegue y verificación funcional.

---

## Trabajo posterior (fuera de este spec)

Detectado en el relevamiento, deliberadamente no incluido. Cada ítem es independiente.

**1 · Instrumentar `gate_post_edit_healer.py` con tokens medidos.**
Hoy escribe `tokens_before=1500` (línea 50) y `tokens_before=500` (línea 62) como constantes.
Los 103 eventos `LINTER_FIX` son 103 × 500 = 51.500 tokens declarados y 0 medidos, o sea el 78 %
del ahorro reportado del sistema es una estimación fija. Otros scripts (`compress_diff.py`,
`prune_terminal_output.py`) ya pasan valores reales a `token_tracker.py`: el healer es la
excepción. Sin esto no hay forma de saber si el sistema rinde.

**2 · Símbolos remotos en el grafo local.**
`tokenix`, `codebase-memory-mcp`, `pyright` y `ruff` indexan sólo el disco local. Sobre un
proyecto que vive en el VPS, la §2 del estándar —resolución LSP previa y grafo de símbolos—
queda inaplicable. `agy-opt vps-index` existe y hace exactamente eso, pero es manual y nadie lo
invoca. Candidato: dispararlo desde `PreInvocation` cuando el workspace sea remoto.

**3 · Gauntlet remoto.**
`./scripts/pre-push.sh` y `pytest --cov` asumen ejecución local. Falta un envoltorio que los
corra en el VPS y devuelva sólo el resumen comprimido, reusando `IRemoteExecutor` de CU-3.

**4 · Caché semántica sobre salidas remotas.**
`semantic_response_cache.py` existe y no se aplica a la capa remota. Un `vps-health` o un
`systemctl status` repetido en la misma sesión podría servirse de caché a $0.

## Contexto precompilado

<!-- Generado por spec_context_bundle.py. El constructor NO necesita releer estos archivos. -->

### Puertos existentes del repositorio

- `src/domain/ports.py` → `ICredentialLoader: load(custom_path)`
- `src/domain/ports.py` → `IModelCascade: get_active_providers(credentials)`
- `src/domain/ports.py` → `IHardwareOptimizer: sync_ramdisk_workspace(repo_dir)`
- `src/domain/ports.py` → `IPostEditHealer: heal_file(target_file)`
- `src/domain/ports.py` → `ISemanticCache: get(query, threshold), set(query, response)`
- `src/domain/ports.py` → `IASTPruner: prune(file_path, content)`
- `src/domain/ports.py` → `ITokenTelemetry: record_event(event), get_summary(), get_recent_events(limit)`
- `src/domain/ports.py` → `IDiffCompressor: compress_diff(diff_content, max_noise_lines)`
- `src/domain/ports.py` → `ISLMHealer: repair_syntax(file_path, code, syntax_error)`
- `src/domain/ports.py` → `ITerminalPruner: prune_output(command, output, exit_code)`
- `src/domain/ports.py` → `IDataSchemaPruner: prune_data_file(file_path, content)`
- `src/domain/ports.py` → `IPolyglotHealer: heal_file(target_file)`

### Contratos a reusar (`src/domain/ports.py:147,228,238`)

```python
@dataclass
class TokenSavingsEvent:
    event_type: str
    tool_name: str
    tokens_before: int
    tokens_after: int
    tokens_saved: int
    latency_ms: float
    timestamp: str


@dataclass
class TerminalPruneResult:
    original_lines: int
    pruned_lines: int
    exit_code: int
    clean_output: str
    reduction_ratio: float


class ITerminalPruner(ABC):
    @abstractmethod
    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult: ...
```

### `skills/token-optimizer/scripts/vps_exec.py`

<!-- esqueleto: 364 B de 3579 B originales -->
```python
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def clean_ansi(text: str) -> str: ...


def compress_vps_output(raw_output: str, max_lines: int = 40) -> str: ...


def run_vps_command(cmd: str, host: str = "vps") -> tuple[int, str]: ...


def main(): ...
```

Defectos conocidos a corregir: `timeout=60` hardcodeado, `capture_output=True` sin TTY,
`host='vps'` sin fallback, y poda inline duplicada en `compress_vps_output` en lugar de
consumir `ITerminalPruner`.

### `skills/token-optimizer/scripts/vps_reader.py`

<!-- esqueleto: 336 B de 2765 B originales -->
```python
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def read_remote_lines(remote_path: str, start_line: int, end_line: int, host: str = "vps") -> str: ...


def read_remote_ast(remote_path: str, host: str = "vps") -> str: ...
```

### `src/adapters/terminal_pruner.py` (adaptador a reusar)

<!-- esqueleto: 747 B de 3213 B originales -->
```python
import re
from typing import List
from src.domain.ports import ITerminalPruner, TerminalPruneResult


class TerminalOutputPruner(ITerminalPruner):
    NOISE_PATTERNS = [...]

    def _is_noise_line(self, line: str) -> bool: ...

    def prune_output(self, command: str, output: str, exit_code: int = 0) -> TerminalPruneResult: ...
```

### Despliegue vigente (`install.sh`)

```bash
DEST_AGENTS="$HOME/.agents"                                        # línea 8
cp -r "$SCRIPT_DIR/plugins/agy-global-optimizer/"* "$DEST_PLUGINS/agy-global-optimizer/"   # 20
cp -r "$SCRIPT_DIR/skills/token-optimizer/"* "$DEST_SKILLS/token-optimizer/"               # 24
cp "$DEST_AGENTS_MD" "$DEST_AGENTS_MD.bak"                          # 32 (patrón de backup)
cp "$SCRIPT_DIR/AGENTS.md" "$DEST_AGENTS_MD"                        # 34
ln -sf "$DEST_SKILLS/token-optimizer/scripts/agy_cli.py" "$HOME/.local/bin/agy-opt"        # 38
```

`hooks/` y `config/hooks.json` son directorios **nuevos**: hoy no existen en el repo.

### Hooks vigentes fuera de versionado (`~/.agents/hooks/`)

| Archivo | Rol | Se toca |
|---|---|---|
| `gate_build_blocker.py` | Gate de permisos; `CRITICAL_COMMAND_PATTERNS:237`, `handle_critical_only:257` | CU-5 |
| `gate_diff_compressor_interceptor.py` | Reescritura de comandos; `process_command:12` | CU-4 |
| `gate_ast_pruner_interceptor.py` | Guardián de lecturas; `check_view_file:13` | CU-6 |
| `gate_pre_invocation.py` | Inyecta `BUILD_DIRECTIVE:41` / `PLAN_DIRECTIVE:29` | Bloque VPS |
| `gate_post_edit_healer.py` | Auto-sanación post-edición (103 eventos `LINTER_FIX`) | sólo versionar |
| `gate_spec_auditor.py` | Auditor SDD post-escritura | sólo versionar |
| `agy_mode.py` | Estado de modo y `audit()` | sólo versionar |

Wiring activo en `~/.gemini/config/hooks.json`, clave `security-hard-gate`, con tres entradas
`PreToolUse` (matchers `write_to_file|replace_file_content|run_command|invoke_subagent|view_file`,
`view_file`, `run_command`), dos `PostToolUse` y una `PreInvocation`.

### Configuración SSH vigente (`~/.ssh/config`)

```
Host vps vps4
    Port 5932
    User root
    IdentityFile ~/.ssh/id_ed25519
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 15m
    Compression yes

Host vps
    HostName 2800:6c0:5::1fbf      # IPv6, alias primario

Host vps4
    HostName 168.181.184.103       # IPv4, fallback — misma máquina
```

El multiplexado ya está bien configurado: no hay costo de handshake por comando. El transporte
no requiere cambios.

### Texto a inyectar en `BUILD_DIRECTIVE` (`gate_pre_invocation.py:41`)

Aproximadamente 45 tokens efímeros por invocación, sin costo de contexto persistente:

```
5. VPS REMOTO: para intervenir el servidor usá 'agy-opt vps-run <cmd>',
   'agy-opt vps-read <archivo> --ast', 'agy-opt vps-patch', 'agy-opt vps-health'.
   Prohibido 'ssh' crudo para consultas: la salida entra sin podar al contexto.
   Comandos interactivos, dumps binarios y operaciones largas sí van por ssh directo.
```
