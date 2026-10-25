# Versionado

Las versiones se escriben `A.n.x`, por ejemplo `1.0.0`. Son tres contadores enteros que empiezan en 0.

**Cada commit que cambia el sitio, el código o la configuración es una versión nueva**, con su etiqueta `vA.n.x` puesta en ese commit. La versión que está en producción es la del commit que corre en el servidor.

**Los commits que solo tocan documentos (`docs/`, `README.md`) no llevan versión**, ni entrada en el `CHANGELOG.md`, ni etiqueta. Su mensaje es `docs: resumen`. Si un commit mezcla documentos con cambios del sitio, lleva versión.

La versión `1.0.0` es la primera que estuvo en producción, del 21 de octubre de 2026.

## Cuándo sube cada número

| Número | Sube cuando | Qué pasa con los de la derecha |
|---|---|---|
| `A` (el primero) | El cambio rompe lo que ya funcionaba: hay que hacer un paso extra al desplegar, o algo anterior deja de servir. | `n` y `x` vuelven a 0 (de `1.4.2` a `2.0.0`). |
| `n` (el de en medio) | Se agrega o cambia algo importante que se nota, sin romper lo anterior. | `x` vuelve a 0 (de `1.0.3` a `1.1.0`). |
| `x` (el último) | Se corrige, se ajusta o se actualiza algo sin agregar nada importante. | Nada. |

### Sube `A`
- La base de datos cambia de forma que la anterior no se puede usar sin migrarla.
- El CSV o el PDF cambian de formato, y lo que alguien armó con ellos deja de servir.
- Cambia la forma de desplegar: otro servidor, otro dominio, otro proceso de arranque.
- Se quita una función que la gente ya usaba.

### Sube `n`
En el sitio:
- Una página o sección nueva.
- Una función nueva, por ejemplo el reproductor de videos.
- Una medida nueva en los resultados.
- Un modelo entrenado nuevo, porque cambian los resultados.
- Un cambio de diseño que se nota.
- Un cambio del nombre del sitio o del proyecto.

### Sube `x`
- Un error de código.
- Un error en un mensaje o en un texto, o la ortografía.
- Un dato de contacto o un enlace roto.
- Un ajuste pequeño de estilo.
- Una actualización de una dependencia por seguridad.
- Un ajuste de configuración del servidor sin efecto visible.

## Cómo decidir

Hazte estas preguntas en este orden y quédate con la primera que se cumpla:

1. ¿El despliegue exige un paso extra, o algo que antes funcionaba deja de funcionar? Sube `A`.
2. ¿Se agrega o cambia algo importante, algo que alguien notaría sin que se lo avisen? Sube `n`.
3. Si no, sube `x`.

Reglas fijas:
- Si un commit mezcla cambios de varios tipos, manda el más alto. Por eso conviene que cada commit trate de un solo tema.
- Solo se sube de uno en uno. No se saltan números y no se bajan.
- Un número ya publicado no se reutiliza. Si una versión salió mal, se corrige con una versión nueva.

## Cómo se registra una versión

1. Elige el número con las reglas de arriba.
2. En `CHANGELOG.md`, agrega la entrada de la versión nueva arriba, con la fecha, el commit y qué cambió. Va en el mismo commit.
3. Haz el commit (si solo toca documentos, no va aquí: ver arriba). El mensaje lleva el tipo, dos puntos, el número de la versión y el resumen: `tipo: vA.n.x resumen`, por ejemplo `fix: v1.4.2 corrige el enlace de contacto`. Los tipos son `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `perf` y `chore`, y se agrega `!` al tipo si sube `A`.
4. Ponle la etiqueta al commit, con un mensaje corto:

   ```bash
   git tag -a vA.n.x -m "Versión A.n.x: qué cambió"
   ```

5. Sube el commit y, aparte, la etiqueta:

   ```bash
   git push origin main
   git push origin vA.n.x
   ```

## Cómo llevar una versión a producción

Actualiza el servidor y reconstruye (ver [`despliegue.md`](despliegue.md)):

```bash
cd ~/imagebio && git pull && docker compose up -d --build
```

Comprueba que el servidor tiene la versión que esperas:

```bash
git describe --tags
```

Debe mostrar `vA.n.x`. Si muestra algo como `vA.n.x-3-gabc1234`, el servidor tiene commits posteriores a la etiqueta.

## Corregir producción cuando `main` ya tiene cambios sin desplegar

Se corrige en una rama que sale de la etiqueta que está en producción, para no desplegar de más:

```bash
git switch -c arreglo-1.0.4 v1.0.3
```

Se hace el arreglo, se etiqueta con el número que le toque y se despliega. Después se junta con `main`.
