#!/usr/bin/env sh

# TODO: ways to make this less crazy when there are multiple targets?
# TODO: include an exclude list of common file names to skip. Like
# package-lock.json, node_modules/

# This file was generated from the code-formatter directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.


## src

last_modified_name="src"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './src/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './src/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black src/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## docs

last_modified_name="docs"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './docs/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './docs/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './docs/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './docs/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black docs/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## example

last_modified_name="example"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './example/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './example/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './example/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './example/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black example/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi


## .github

last_modified_name=".github"
last_modified_name=$(echo $last_modified_name | sed 's^/^-^g')
if [ -e .last-modified/$last_modified_name-prettier ]; then
  modified_files_prettier=$(find . \( \
      -newer .last-modified/$last_modified_name-prettier \
      -type f -readable -writable \
      -path './.github/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
else
  modified_files_prettier=$(find . \( \
      -type f -readable -writable \
      -path './.github/*' \
    \) \( \
      -name '*.js' \
      -o -name '*.jsx' \
      -o -name '*.mjs' \
      -o -name '*.ts' \
      -o -name '*.tsx' \
      -o -name '*.css' \
      -o -name '*.less' \
      -o -name '*.scss' \
      -o -name '*.json' \
      -o -name '*.graphql' \
      -o -name '*.gql' \
      -o -name '*.markdown' \
      -o -name '*.md' \
      -o -name '*.mdown' \
      -o -name '*.mkd' \
      -o -name '*.mkdn' \
      -o -name '*.mdx' \
      -o -name '*.vue' \
      -o -name '*.svelte' \
      -o -name '*.yml' \
      -o -name '*.yaml' \
      -o -name '*.html' \
      -o -name '*.php' \
      -o -name '*.rb' \
      -o -name '*.ruby' \
      -o -name '*.xml' \
    \) -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-prettier
fi
if [ -n "$modified_files_prettier" ]; then
  npm run prettier -- --write $modified_files_prettier
  echo "$(date)" > .last-modified/$last_modified_name-prettier
fi

if [ -e .last-modified/$last_modified_name-black ]; then
  modified_files_black=$(find . \( \
      -newer .last-modified/$last_modified_name-black \
      -type f -readable -writable \
      -path './.github/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
else
  modified_files_black=$(find . \( \
      -type f -readable -writable \
      -path './.github/*' \
    \) \
    -name '*.py' \
    -nowarn \
    || printf '')
  touch .last-modified/$last_modified_name-black
fi
if [ -n "$modified_files_black" ]; then
  black .github/
  echo "$(date)" > .last-modified/$last_modified_name-black
fi
