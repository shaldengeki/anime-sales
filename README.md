anime_sales
===========

Anime sales data parser. Supports only oricon-style lists at the moment.

To get started, place your textfiles in `data/SOURCE_NAME/year-month-day.txt`

For example:

    import anime_sales
    salesData = anime_sales.Sales()
    salesData.load()
    gintamaName = salesData.search('gintama')[0]
    print salesData.series(gintamaName).sales(fields=['id', 'sales', 'date']).sales()
    salesData.series(gintamaName).sales().save('gintama-sales')

Licensed under the WTFPL.