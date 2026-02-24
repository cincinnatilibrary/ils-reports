CREATE VIEW IF NOT EXISTS genre_view AS
WITH genre_data AS (
    SELECT
        bib.bib_record_num,
        json_each.value AS genre -- ,
    -- count(item.item_record_num)
    FROM
        bib,
        JSON_EACH(bib.genres)
)

SELECT
    d.genre,
    COUNT(d.bib_record_num) AS count_bibs,
    JSON_OBJECT(
        'href',
        '/current_collection/bib?_sort=bib_record_num&genres__arraycontains=' || d.genre,
        'label',
        'bibs with this genre'
    ) AS link
FROM
    genre_data AS d
GROUP BY
    d.genre;
