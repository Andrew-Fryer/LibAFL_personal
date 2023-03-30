for f in crashes/*; do cat "${f}" | ./knotd_stdio; echo "exit code:"$?; done | grep "exit code"
