# ChandraGen
Designed for terminal browser enthusiasts, ChandraGen bridges MDX-based frameworks with geminispace. It enables users to explore a new dimension of your site, similar to how the Chandra X-Ray Observatory—its namesake—uncovered a new visual layer of the cosmos.

ChandraGen originated as a straightforward conversion script that dynamically created a gemini page from the markdown document housing the https://allthingslinux.org code of conduct. As the scope of the gemini capsule project I oversee for that organization expanded, it became apparent that a framework of this nature was essential, yet no options suited our needs. Consequently, I have undertaken this project personally. I hope you find ChandraGen beneficial!

## Using Chandragen

Chandragen is built around a robust core: a distributed job queue system. Consequently, Chandragen relies on a shared database to manage worker process states. It is expected to migrate to Redis in the future, but for now, it uses a familiar setup. 

Chandragen consists of two main components: workers, which execute formatting tasks, and schedulers, which assign jobs to the workers. Currently, these components operate separately to facilitate testing on cluster compute setups, with plans to streamline the system in future updates.

To use Chandragen, ensure you have a PostgreSQL instance configured. You can set it up according to your requirements but remember to provide a valid URL for it in the `.env` file. To start a pool of worker processes with access to the necessary filesystems, run `poetry run chandragen run-pooler`. Then, use `poetry run chandragen run-config [path to config]` to load the TOML formatter configuration into the queue using the one-shot scheduler.

## Configurability
The config system is currecntly hardcoded to the formatter system. expect large changes post-0.1
Use the example config to see what keys it supports. ChandraGen supports setting as many targets as you want, both as dirs anf files. the recursive flag can be set on a dir entry to have it recursively grab every formattable file it can find. the config must have a default config defined, which can then have sections overridden under the config for each target.

## Extensibility
ChandraGen supports external formatters via a plugin system. you can find an example plugin in the plugins directory. plugin formatters can be called the same way as internal formatters in the configuration. you can use `poetry run chandragen list-formatters` to get the currently available internal and external formatters. built-in formatter documentation is in the works.

## Planned
- Integrated Perigee CGI framework
  - An orbit's perigee is where it comes the closest to a celestial body, making it an ideal name for a framework sitting very close to the end user
  - support for invoking ChandraGen formatters on a document to produce the results to pass to the user
  - integrated module loader with hotloading
  - handling for databases via prisma
- API for triggering document rebuilds
- Far down the line, possibly an integrated gemini server
- Extensibility to support formats other than MD(X)
