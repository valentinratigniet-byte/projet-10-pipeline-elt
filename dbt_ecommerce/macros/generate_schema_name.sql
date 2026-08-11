{#
  Par défaut dbt préfixe le schéma cible (ex. "analytics_marts").
  On veut des schémas propres et stables : "staging" et "marts".
  Ce macro utilise le +schema du modèle tel quel.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
