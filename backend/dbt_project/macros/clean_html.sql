{% macro clean_html(column_name) %}
{#
    Strip HTML tags and decode common HTML entities from text content.

    Args:
        column_name: The column containing HTML text to clean.

    Returns:
        Cleaned text with HTML tags removed, entities decoded, and
        whitespace normalized. Returns NULL if input is NULL.

    Supported entities:
        - Named: &lt; &gt; &amp; &quot; &nbsp; &apos;
        - Numeric: &#39; &#34; &#38; &#60; &#62; &#160;
        - Hex: &#x27; &#x22; &#x26; &#x3c; &#x3e; &#xa0;
#}
case
    when {{ column_name }} is null then null
    else
        trim(
            regexp_replace(
                regexp_replace(
                    regexp_replace(
                        regexp_replace(
                            regexp_replace(
                                regexp_replace(
                                    regexp_replace(
                                        regexp_replace(
                                            regexp_replace(
                                                regexp_replace(
                                                    regexp_replace(
                                                        regexp_replace(
                                                            regexp_replace(
                                                                regexp_replace(
                                                                    regexp_replace(
                                                                        regexp_replace(
                                                                            regexp_replace(
                                                                                regexp_replace(
                                                                                    regexp_replace(
                                                                                        regexp_replace(
                                                                                            {{ column_name }},
                                                                                            '<[^>]+>', '', 'g'
                                                                                        ),
                                                                                        '&lt;', '<', 'g'
                                                                                    ),
                                                                                    '&gt;', '>', 'g'
                                                                                ),
                                                                                '&amp;', '&', 'g'
                                                                            ),
                                                                            '&quot;', '"', 'g'
                                                                        ),
                                                                        '&nbsp;', ' ', 'g'
                                                                    ),
                                                                    '&apos;', '''', 'g'
                                                                ),
                                                                '&#39;', '''', 'g'
                                                            ),
                                                            '&#x27;', '''', 'gi'
                                                        ),
                                                        '&#34;', '"', 'g'
                                                    ),
                                                    '&#x22;', '"', 'gi'
                                                ),
                                                '&#38;', '&', 'g'
                                            ),
                                            '&#x26;', '&', 'gi'
                                        ),
                                        '&#60;', '<', 'g'
                                    ),
                                    '&#x3[cC];', '<', 'g'
                                ),
                                '&#62;', '>', 'g'
                            ),
                            '&#x3[eE];', '>', 'g'
                        ),
                        '&#160;|&#x[aA]0;', ' ', 'g'
                    ),
                    '[\r\n]+', ' ', 'g'
                ),
                ' +', ' ', 'g'
            )
        )
end
{% endmacro %}
