{% macro surrogate_key(columns) -%}
    md5(
        {%- for col in columns -%}
            coalesce(cast({{ col }} as text), '')
            {%- if not loop.last %} || '|' || {% endif -%}
        {%- endfor -%}
    )
{%- endmacro %}