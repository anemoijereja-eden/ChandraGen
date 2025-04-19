# ChandraGen
Built for quiet web enthusiasts, ChandraGen connects existing MDX-based frameworks to geminispace.
ChandraGen allows users to see a new layer of your site, similarly to how the Chandra X-Ray observatory it's named after revealed a new visual layer of the cosmos.

ChandraGen started as a simple converter script that built a gemini page dynamically from the markdown document used to house the https://allthingslinux.org code of conduct. as the scope of thegemini capsule project I head for that organization grew, it became clear that a framework like this would be necessary, but I found no options for it that fit our usecase. as such, I've taken the project on myself. I hope you're able to find ChandraGen useful!

# The codebase
ChandraGen is build entirely using python simply because that's the best language I know for string manipulation. the formatting system is simple enough that it still runs pretty fast without excessive overhead despite being in python. 

# TODO:
- Write the config parser and logic for batching and formatting files as defined by a configuration
- Add additional formatters to handle inline markdown links
- Find a way to add conversion hints and gemini-only tags to an mdx document, and implement parsing for them
- Write a Dockerfile for this, make it integrate cleanly in a docker compose that builds ChandraGen and a gemini server line Gemserv
- Integration with common MDX-based http ssg frameworks
- Contributor documentation
- CI, Linting, Strict type checking, and dependency management