+++
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
date = {{ .Date }}
draft = true
+++

{{ if .Draft }}
    {{< notice tip >}}
        Test
    {{< /notice >}}
{{ end }}