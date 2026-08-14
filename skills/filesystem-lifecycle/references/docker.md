# Docker storage

Treat images, build cache, containers, volumes, and Docker's sparse disk image as different resources.

## Generic reclaim ceiling

Generic RECLAIM may consider only verified-unused images and build cache. Prefer narrow owner operations:

```bash
docker image prune
docker builder prune
```

Do not run `docker system prune`, `docker container prune`, or any prune with `--volumes` unless containers and volumes were separately inventoried, classified, and authorized. A stopped container can retain useful writable-layer state.

Never manually delete `Docker.raw`. Do not trust Docker's reclaim estimate as physical APFS recovery; remeasure the target volume and verify running services afterward.

## Required evidence

Record daemon reachability, running and stopped containers, image references, builder cache ownership, volume-to-container relationships, database roles, and exact authorization. If the daemon is unavailable or the inventory is incomplete, classify Docker resources `unknown`.
