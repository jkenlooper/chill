# Loading and Dumping of Chill Data as YAML files

The `chill dump` and `chill load` scripts will dump and load the chill database as
ChillNode objects in a yaml file.

Dump to the `example-data.yaml` file while in a project folder with
a site.cfg using this command:

```bash
chill dump --config site.cfg --yaml example-data.yaml
```

Depending on the existing database, it will output a YAML file with all the
chill data needed in order to load back into the database. Note that it doesn't
keep track of any node ids in the YAML file. Duplicate routes and nodes will be
added if the YAML file is loaded back into a database that already has the chill
data.

With a fresh database; load it with the ChillNode objects from the
`example-data.yaml` file.

```bash
chill load --config site.cfg --yaml example-data.yaml
```
