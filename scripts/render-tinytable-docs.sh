#!/usr/bin/env bash
# Regenerate the exercises that emit tinytable assets.
#
# modelsummary's datasummary_skim() draws inline sparklines as small PNGs and
# tinytable writes them to a shared tinytable_assets/ folder next to the source,
# CLEARING that folder on every render. When two documents in the same folder
# both produce sparklines, a project-wide render leaves only the last one's
# assets and the earlier document's <img> tags dangle.
#
# So: render each document on its own and accumulate its assets into a union
# folder, which is what gets committed and published. The random asset ids make
# the union safe. Committed _freeze/ results keep each document's HTML pinned to
# the ids it was rendered with.
#
# Run from the repository root after changing any of these documents.
set -euo pipefail

cd "$(dirname "$0")/.."

export RENV_CONFIG_AUTOLOADER_ENABLED=FALSE
export R_PROFILE_USER=/dev/null

DOCS=(
  "ae/ae04-multiple-regression-part-1/ae04-01-MLR.Rmd"
  "ae/ae04-multiple-regression-part-1/ae04-03-hedonic-land-prices-HW.Rmd"
  "ae/ae05-multiple-regression-part-2/ae05-01-OVB.rmd"
  "ae/ae05-multiple-regression-part-2/ae05-03-hedonic-complete-reg-analysis.Rmd"
  "ae/ae06-multiple-regression-part-3/ae06-02-interaction-continuous.rmd"
  "ae/ae06-multiple-regression-part-3/ae06-03-simpsons-paradox.rmd"
)

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

for doc in "${DOCS[@]}"; do
  dir="$(dirname "$doc")"
  stem="$(basename "${doc%.*}")"

  echo "==> $doc"
  rm -rf "_freeze/${dir}/${stem}"
  quarto render "$doc" --to html >/dev/null

  # Quarto treats tinytable_assets/ as a supporting directory: it moves it into
  # _site and removes it from the source tree. So harvest from the output, and
  # fall back to the source in case that behaviour ever changes.
  found=0
  for src in "_site/$dir/tinytable_assets" "$dir/tinytable_assets"; do
    if [ -d "$src" ]; then
      mkdir -p "$STAGE/$dir"
      cp -a "$src/." "$STAGE/$dir/"
      found=$(ls "$src" | wc -l)
      break
    fi
  done
  echo "    harvested $found asset(s)"
done

echo
echo "==> merging accumulated assets"
for dir in $(printf '%s\n' "${DOCS[@]}" | xargs -n1 dirname | sort -u); do
  if [ -d "$STAGE/$dir" ]; then
    mkdir -p "$dir/tinytable_assets"
    cp -a "$STAGE/$dir/." "$dir/tinytable_assets/"
    echo "    $dir/tinytable_assets: $(ls "$dir/tinytable_assets" | wc -l) files"
  fi
done

echo
echo "Done. Run 'quarto render' to rebuild the site with the frozen results."
