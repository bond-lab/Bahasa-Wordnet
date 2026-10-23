# Redirect for the old SourceForge web page

Upload `index.html` over the old pages at <https://wn-msa.sourceforge.net/>
(SourceForge project web space, needs the project admin's login):

    scp index.html USER@web.sourceforge.net:/home/project-web/wn-msa/htdocs/
    for f in index.eng.html index.zsm.html eng/index.html zsm/index.html; do
        scp index.html USER@web.sourceforge.net:/home/project-web/wn-msa/htdocs/$f
    done
