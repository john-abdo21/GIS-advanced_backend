# SELECT 
#     plot.geom AS plot_geom,
#     river.geom AS river_geom,
#     forest.geom AS forest_geom
# FROM 
#     test_pl_plot3857_small AS plot
#     LEFT JOIN test_pl_river3857_small AS river ON ST_DWithin(ST_Transform(plot.geom, 3857), ST_Transform(river.geom, 3857), 1)
#     LEFT JOIN test_pl_forest3857_small AS forest ON ST_DWithin(ST_Transform(plot.geom, 3857), ST_Transform(forest.geom, 3857), 1)
# WHERE 
#     plot.area >= 10000.0
#     AND plot.aed <= 100.0
#     AND plot.aed >= 10.0
#     AND ST_Intersects(ST_Transform(plot.geom, 3857), (
# 				SELECT ST_Union(ST_Transform(geom, 3857))
# 				FROM
# 						test_pl_plot3857_small
# 				INNER JOIN (
# 						SELECT ST_Buffer(ST_Union(ST_Transform(geom, 3857)), 1000.0) AS buffer_test_pl_river3857_small_geom
# 						FROM test_pl_river3857_small
# 				)
# 				AS buffer_test_pl_river3857_small
# 				ON ST_Intersects(ST_Transform(test_pl_plot3857_small.geom, 3857), buffer_test_pl_river3857_small.buffer_test_pl_river3857_small_geom)
# 				INNER JOIN (
# 						SELECT ST_Buffer(ST_Union(ST_Transform(geom, 3857)), 1000.0) AS buffer_test_pl_forest3857_small_geom
# 						FROM test_pl_forest3857_small
# 				)
# 				AS buffer_test_pl_forest3857_small
# 				ON ST_Intersects(test_pl_plot3857_small.geom, buffer_test_pl_forest3857_small.buffer_test_pl_forest3857_small_geom)
# 				WHERE test_pl_plot3857_small.area >= 10000.0
# 				AND test_pl_plot3857_small.aed <= 100.0 AND test_pl_plot3857_small.aed >= 10.0
# 		)
# );

from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from django.http import JsonResponse,StreamingHttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import PlRiver3857, PlPlot3857,Inlandwater,PlPlot3857
# from .serializers import *
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers import serialize
from django.contrib.gis.measure import D
import json

from django.contrib.gis.db.models.functions import Transform, Area, Distance
import json
import random
import logging

# Create your views here.

# def front(request):
#     context = { }
#     return render(request, "index.html", context)

def executeSQL(title, query):
    query += ''';'''
    print(title, query)
    with connection.cursor() as cursor:
        cursor.execute(query)
        overlapping_regions = cursor.fetchall()
    return overlapping_regions


@api_view(['GET', 'POST'])
def complex_Search(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK)
    elif request.method == 'POST':
        print('complex search',request.data)

        # Importing variables
        data = request.data.get('data')

        land_option = data['landOption']
        l_min_area = land_option['l_min_area']
        l_max_area = land_option['l_max_area']
        l_min_aed = land_option['l_min_aed']
        l_max_aed = land_option['l_max_aed']

        options = data['options']

        f_min_distance = options['forest']['minDistance']
        f_max_distance = options['forest']['maxDistance']
        f_min_area = options['forest']['minArea']
        f_max_area = options['forest']['maxArea']

        r_min_distance = options['river']['minDistance']
        r_max_distance = options['river']['maxDistance']
        r_min_length = options['river']['minLength']
        r_max_length = options['river']['maxLength']
        r_min_width = options['river']['minWidth']
        r_max_width = options['river']['maxWidth']

        i_min_distance = options['lake']['minDistance']
        i_max_distance = options['lake']['maxDistance']
        i_min_area = options['lake']['minArea']
        i_max_area = options['lake']['maxArea']

        t_min_distance = options['town']['minDistance']
        t_max_distance = options['town']['maxDistance']
        t_min_area = options['town']['minArea']
        t_max_area = options['town']['maxArea']
        t_hospital_exist = options['town']['hospital']
        t_station_exist = options['town']['station']
        t_hospital_distance = options['town']['hospitalDistance']
        t_station_distance = options['town']['stationDistance']
        t_school_distance = options['town']['schoolDistance']
        t_hospital_label = options['town']['hospitalLabel']
        t_station_label = options['town']['stationLabel']
        t_school_label = options['town']['schoolLabel']

        # Transforming the data unit
        if l_min_area:
            l_min_area = float(l_min_area) * 10000
        if l_max_area:
            l_max_area = float(l_max_area) * 10000
        if l_min_aed:
            l_min_aed = float(l_min_aed)
        if l_max_aed:
            l_max_aed = float(l_max_aed)

        if r_min_distance:
            r_min_distance = float(r_min_distance) * 1000
        if r_max_distance:
            r_max_distance = float(r_max_distance) * 1000

        if f_min_distance:
            f_min_distance = float(f_min_distance) * 1000
        if f_max_distance:
            f_max_distance = float(f_max_distance) * 1000
        if f_min_area:
            f_min_area = float(f_min_area) * 10000
        if f_max_area:
            f_max_area = float(f_max_area) * 10000

        if i_min_distance:
            i_min_distance = float(i_min_distance) * 1000
        if i_max_distance:
            i_max_distance = float(i_max_distance) * 1000
        if i_min_area:
            i_min_area = float(i_min_area) * 10000
        if i_max_area:
            i_max_area = float(i_max_area) * 10000

        if t_hospital_distance:
            t_hospital_distance = float(t_hospital_distance) * 1000
        if t_station_distance:
            t_station_distance = float(t_station_distance) * 1000
        if t_school_distance:
            t_school_distance = float(t_school_distance) * 1000

        sqlForRegions = ''''''
        sqlForRast = ''''''
        sqlForRiver = ''''''
        sqlForForest = ''''''
        sqlForInlandwater = ''''''
        sqlForHospital = ''''''

        plot_table = 'test_pl_plot3857_small'
        forest_table = 'test_pl_forest3857_small'
        river_table = 'test_pl_river3857_small'
        lake_table = 'test_pl_inlandwater3857_small'
        other_table = 'test_pl_hospital3857_small'

        area_field = 'area'
        length_field = 'length'
        width_field = 'width'
        geom_field = 'geom'
        object_field = 'amenity'
        aed_field = 'aed'

        # SQL query generates
        sqlSelectPart = '''
            ST_AsGeoJSON(ST_Transform({}, 3857)), "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"
        '''.format(geom_field)
        # sqlSelectPart = '''
        #     ST_AsGeoJSON(ST_Transform({}, 3857))
        # '''.format(geom_field)

        l_where_SQL = ''''''
        if l_min_area or l_max_area:
            if l_min_area == '':
                l_where_SQL = '''
                    WHERE {}.{} <= {}
                '''.format(plot_table, area_field, l_max_area)
            elif l_max_area == '':
                l_where_SQL = '''
                    WHERE {}.{} >= {}
                '''.format(plot_table, area_field, l_min_area)
            elif l_min_area <= l_max_area:
                l_where_SQL = '''
                    WHERE {}.{} >= {} AND {}.{} <= {}
                '''.format(plot_table, area_field, l_min_area, plot_table, area_field, l_max_area)
            else:
                l_where_SQL = '''
                    WHERE {}.{} >= 0
                '''.format(plot_table, area_field)
        else:
            l_where_SQL = '''
                WHERE {}.{} >= 0
            '''.format(plot_table, area_field)

        if l_min_aed or l_max_aed:
            if l_min_aed == '':
                l_where_SQL += '''
                    AND {}.{} <= {}
                '''.format(plot_table, aed_field, l_max_aed)
            elif l_max_aed == '':
                l_where_SQL += '''
                    AND {}.{} >= {}
                '''.format(plot_table, aed_field, l_min_aed)
            elif l_min_aed <= l_max_aed:
                print(l_min_aed, l_max_aed)
                l_where_SQL += '''
                    AND {}.{} <= {} AND {}.{} >= {}
                '''.format(plot_table, aed_field, l_max_aed, plot_table, aed_field, l_min_aed)
        
        sqlForRegions = '''
            SELECT
        '''
        sqlForRegions += sqlSelectPart
        sqlForRegions += '''
            FROM
                {}
        '''.format(plot_table)


        r_where_SQL = ''''''
        if r_min_length or r_max_length:
            if r_min_length == '':
                r_where_SQL = '''
                    WHERE {}.{} <= {}
                '''.format(river_table, length_field, r_max_length)
            elif r_max_length == '':
                r_where_SQL = '''
                    WHERE {}.{} >= {}
                '''.format(river_table, length_field, r_min_length)
            elif r_min_length <= r_max_length:
                r_where_SQL = '''
                    WHERE {}.{} >= {} AND {}.{} <= {}
                '''.format(river_table, length_field, r_min_length, river_table, length_field, r_max_length)

        if r_min_width or r_max_width:
            if r_where_SQL:
                if r_min_width == '':
                    r_where_SQL += '''
                        AND {}.{} <= {}
                    '''.format(river_table, width_field, r_max_width)
                elif r_max_width == '':
                    r_where_SQL += '''
                        AND {}.{} >= {}
                    '''.format(river_table, width_field, r_min_width)
                elif r_min_width <= r_max_width:
                    r_where_SQL += '''
                        AND {}.{} >= {} AND {}.{} <= {}
                    '''.format(river_table, width_field, r_min_width, river_table, width_field, r_max_width)
            else:
                if r_min_width == '':
                    r_where_SQL = '''
                        WHERE {}.{} <= {}
                    '''.format(river_table, width_field, r_max_width)
                elif r_max_width == '':
                    r_where_SQL = '''
                        WHERE {}.{} >= {}
                    '''.format(river_table, width_field, r_min_width)
                elif r_min_width <= r_max_width:
                    r_where_SQL = '''
                        WHERE {}.{} >= {} AND {}.{} <= {}
                    '''.format(river_table, width_field, r_min_width, river_table, width_field, r_max_width)

        if r_min_distance or r_max_distance:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, r_max_distance, river_table, geom_field, river_table)
            sqlForRegions += r_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects(ST_Transform({}.{}, 3857), buffer_{}.buffer_{}_{})
            '''.format(river_table, plot_table, geom_field, river_table, river_table, geom_field)
        elif r_where_SQL:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), 0.00001) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, river_table, geom_field, river_table)
            sqlForRegions += r_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects(ST_Transform({}.{}, 3857), buffer_{}.buffer_{}_{})
            '''.format(river_table, plot_table, geom_field, river_table, river_table, geom_field)

        i_where_SQL = ''''''
        if i_min_area or i_max_area:
            if i_min_area == '':
                i_where_SQL = '''
                    WHERE {} <= {}
                '''.format(area_field, i_max_area)
            elif i_max_area == '':
                i_where_SQL = '''
                    WHERE {} >= {}
                '''.format(area_field, i_min_area)
            elif i_min_area <= i_max_area:
                i_where_SQL = '''
                    WHERE {} >= {} AND {} <= {}
                '''.format(area_field, i_min_area, area_field, i_max_area)

        if i_min_distance or i_max_distance:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, i_max_distance, lake_table, geom_field, lake_table)
            sqlForRegions += i_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects({}.{}, buffer_{}.buffer_{}_{})
            '''.format(lake_table, plot_table, geom_field, lake_table, lake_table, geom_field)
        elif i_where_SQL:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), 0.00001) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, lake_table, geom_field, lake_table)
            sqlForRegions += i_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects({}.{}, buffer_{}.buffer_{}_{})
            '''.format(lake_table, plot_table, geom_field, lake_table, lake_table, geom_field)
        
        f_where_SQL = ''''''
        if f_min_area or f_max_area:
            if f_min_area == '':
                f_where_SQL = '''
                    WHERE {} <= {}
                '''.format(area_field, f_max_area)
            elif f_max_area == '':
                f_where_SQL = '''
                    WHERE {} >= {}
                '''.format(area_field, f_min_area)
            elif f_min_area <= f_max_area:
                f_where_SQL = '''
                    WHERE {} >= {} AND {} <= {}
                '''.format(area_field, f_min_area, area_field, f_max_area)
        
        if f_min_distance or f_max_distance:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, f_max_distance, forest_table, geom_field, forest_table)
            sqlForRegions += f_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects({}.{}, buffer_{}.buffer_{}_{})
            '''.format(forest_table, plot_table, geom_field, forest_table, forest_table, geom_field)
        elif f_where_SQL:
            sqlForRegions += '''
                INNER JOIN (
                    SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), 0.00001) AS buffer_{}_{}
                    FROM {}
                '''.format(geom_field, forest_table, geom_field, forest_table)
            sqlForRegions += f_where_SQL
            sqlForRegions += '''
                )
            '''
            sqlForRegions += '''
                AS buffer_{}
                ON ST_Intersects({}.{}, buffer_{}.buffer_{}_{})
            '''.format(forest_table, plot_table, geom_field, forest_table, forest_table, geom_field)

        if t_hospital_label or t_station_label or t_school_label:
            if t_hospital_distance:
                sqlForRegions += '''
                    INNER JOIN (
                        SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}_hospital
                        FROM {}
                        WHERE {} = 'hospital'
                    )
                    AS buffer_{}_hospital
                    ON ST_Intersects({}.{}, buffer_{}_hospital.buffer_{}_{}_hospital)
                '''.format(geom_field, t_hospital_distance, other_table, geom_field, other_table, object_field, other_table, plot_table, geom_field, other_table, other_table, geom_field)
            if t_station_distance:
                sqlForRegions += '''
                    INNER JOIN (
                        SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}_station
                        FROM {}
                        WHERE {} = 'bus_station'
                    )
                    AS buffer_{}_station
                    ON ST_Intersects({}.{}, buffer_{}_station.buffer_{}_{}_station)
                '''.format(geom_field, t_station_distance, other_table, geom_field, other_table, object_field, other_table, plot_table, geom_field, other_table, other_table, geom_field)
            if t_school_distance:
                sqlForRegions += '''
                    INNER JOIN (
                        SELECT ST_Buffer(ST_Union(ST_Transform({}, 3857)), {}) AS buffer_{}_{}_school
                        FROM {}
                        WHERE {} LIKE %%_school
                    )
                    AS buffer_{}_school
                    ON ST_Intersects({}.{}, buffer_{}_school.buffer_{}_{}_school)
                '''.format(geom_field, t_school_distance, other_table, geom_field, other_table, object_field, other_table, plot_table, geom_field, other_table, other_table, geom_field)
        sqlForRegions += l_where_SQL

        # if r_min_length or r_max_length or r_min_width or r_max_width or r_min_distance or r_max_distance:
        #     sqlForRiver = '''
        #         SELECT
        #             ST_AsGeoJSON({})
        #         FROM
        #             {}
        #         WHERE
        #             ST_Intersects({}.{}, (
        #     '''.format(geom_field, river_table, river_table, geom_field)
        #     sqlForRiver += sqlForRegions.replace(', "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"', '').replace('ST_AsGeoJSON','ST_Union')
        #     sqlForRiver += '''))'''

        # if f_min_area or f_max_area or f_min_distance or f_max_distance:
        #     sqlForForest = '''
        #         SELECT
        #             ST_AsGeoJSON({})
        #         FROM
        #             {}
        #         WHERE
        #             ST_Intersects(st_transform({}.{}, 3857), (
        #     '''.format(geom_field, forest_table, forest_table, geom_field)
        #     sqlForForest += sqlForRegions.replace(', "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"', '').replace('ST_AsGeoJSON','ST_Union')
        #     sqlForForest += '''))'''

        # if i_min_distance or i_max_distance or i_min_area or i_max_area:
        #     sqlForInlandwater = '''
        #         SELECT
        #             ST_AsGeoJSON({})
        #         FROM
        #             {}
        #         WHERE
        #             ST_Intersects(st_transform({}.{}, 3857), (
        #     '''.format(geom_field, lake_table, lake_table, geom_field)
        #     sqlForInlandwater += sqlForRegions.replace(', "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"', '').replace('ST_AsGeoJSON','ST_Union')
        #     sqlForInlandwater += '''))'''

        # if t_hospital_label:
        #     sqlForHospital = '''
        #         SELECT
        #             ST_AsGeoJSON({})
        #         FROM
        #             {}
        #         WHERE
        #             ST_Intersects(st_transform({}.{}, 3857), (
        #     '''.format(geom_field, other_table, other_table, geom_field)
        #     sqlForHospital += sqlForRegions.replace(', "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"', '').replace('ST_AsGeoJSON', 'ST_Union')
        #     sqlForHospital += '''))'''
        sqlForUnion = ''
        # sqlForUnion = sqlForRegions.replace(', "ID_DZIALKI", "NAZWA_OBREBU", "NAZWA_GMINY", "area", "aed"', '').replace('ST_AsGeoJSON(ST_Transform(geom, 3857)', 'ST_AsGeoJSON(ST_Union(ST_Transform(geom, 3857))')
        
        json_land = ''
        json_forest = ''
        json_river = ''
        json_inlandwater = ''
        json_others = ''
        json_union = ''
        json_rast = ''

        if sqlForRegions:
            json_land = executeSQL('land', sqlForRegions)

        if sqlForRiver:
            json_river = executeSQL('river', sqlForRiver)

        if sqlForForest:
            json_forest = executeSQL('forest', sqlForForest)

        if sqlForInlandwater:
            json_inlandwater = executeSQL('lake', sqlForInlandwater)

        if sqlForUnion:
            json_union = executeSQL('union', sqlForUnion)

        if sqlForHospital:
            json_union = executeSQL('other', sqlForHospital)
        
        json_data = [
            json_land,
            json_forest,
            json_river,
            json_inlandwater,
            json_others,
            json_union,
            json_rast
        ]

        return JsonResponse(json_data, safe=False)
    
@api_view(['GET', 'POST'])
def all_Search(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK)
    elif request.method == 'POST':
        print('river req')
        print(request.data)
        data = request.data.get('data')
        r_length = data.get('R_length')
        r_width = data.get('R_width')
        l_area_min = data.get('L_Area_min')
        l_area_max = data.get('L_Area_max')
        f_area_min = data.get('F_Area_min')
        f_area_max = data.get('F_Area_max')
        p_area_min = data.get('P_Area_min')
        p_area_max = data.get('P_Area_max')
        json_data=[]
        if r_length:
            if r_width:
                sqlForRiver = '''
                        SELECT ST_AsGeoJSON(ST_Union(geom)) FROM test_pl_river3857_small WHERE dlug >= %(r_length)s and r_width >= %(r_width)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForRiver, {'r_length': r_length,'r_width': r_width})
                    riverfilter = cursor.fetchall()
                print("river_count1" )
            else:
                sqlForRiver = '''
                        SELECT ST_AsGeoJSON(ST_Union(geom)) FROM test_pl_river3857_small WHERE dlug >= %(r_length)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForRiver, {'r_length': r_length})
                    riverfilter = cursor.fetchall()
                    print("river_count2" )
            json_data = json.dumps({'key':'R','val':riverfilter})
        elif l_area_min:
            if l_area_max:
                sqlForLake = '''
                        SELECT ST_AsGeoJSON(ST_Transform(shape, 3857)) FROM inlandwater WHERE area >= %(l_Area_min)s and area <= %(l_Area_max)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForLake, {'l_Area_min': l_area_min,'l_Area_max': l_area_max})
                    lakefilter = cursor.fetchall()
                print("lake_count1" )
            else:
                sqlForLake = '''
                        SELECT ST_AsGeoJSON(ST_Transform(shape, 3857)) FROM inlandwater WHERE area >= %(l_Area_min)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForLake, {'l_Area_min': l_area_min})
                    lakefilter = cursor.fetchall()
                    print("lake_count2" )
            json_data = json.dumps({'key':'L','val':lakefilter})
        elif f_area_min:
            if f_area_max:
                sqlForForest = '''
                    SELECT ST_AsGeoJSON(ST_Transform(way, 3857)) FROM test_pl_forest3857_small WHERE way_area >= %(f_Area_min)s AND way_area <= %(f_Area_max)s;
                '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForForest, {'f_Area_min': f_area_min,'f_Area_max': f_area_max})
                    forestfilter = cursor.fetchall()
                print("forest_count1" ) 
            else:
                sqlForForest = '''
                        SELECT ST_AsGeoJSON(ST_Transform(way, 3857)) FROM test_pl_forest3857_small WHERE way_area >= %(f_Area_min)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForForest, {'f_Area_min': f_area_min})
                    forestfilter = cursor.fetchall()
                    print("forest_count2" )
            json_data = json.dumps({'key':'F','val':forestfilter})
        elif p_area_min:
            if p_area_max:
                sqlForLand = '''
                        SELECT ST_AsGeoJSON(geom) FROM test_pl_plot3857_small WHERE area >= %(p_Area_min)s AND area <= %(p_Area_max)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForLand, {'p_Area_min': p_area_min,'p_Area_max': p_area_max})
                    landfilter = cursor.fetchall()
                print("land_count1" ) 
            else:
                sqlForLand = '''
                        SELECT ST_AsGeoJSON(geom) FROM test_pl_plot3857_small WHERE area >= %(p_Area_min)s;
                    '''
                with connection.cursor() as cursor:
                    cursor.execute(sqlForLand, {'p_Area_min': p_area_min})
                    landfilter = cursor.fetchall()
                    print(landfilter[0])
                print("land_count1" ) 
            json_data = json.dumps({'key':'P','val':landfilter})
        return JsonResponse(json_data, safe=False)

@api_view(['GET', 'POST'])
def point_Search(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK)
    elif request.method == 'POST':
        print('river req')
        print(request.data)
        json_data=[]
        datas = request.data.get('data')
        data=datas['data']
        # sqlForHospital = '''
        #         SELECT ST_AsGeoJSON(ST_Transform(way, 3857)) FROM test_pl_hospital3857_small WHERE amenity=%(parameter)s;
        #     '''
        sqlForHospital = '''

        '''
        with connection.cursor() as cursor:
            cursor.execute(sqlForHospital,{'parameter':data})
            datafilter = cursor.fetchall()
        print(data) 
        json_data = json.dumps({'key':data,'val':datafilter})
        return JsonResponse(json_data, safe=False)

@api_view(['GET', 'POST'])
def advanced_Search(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK)
    elif request.method == 'POST':
        print('advanced Search')
        print(request.data)
        json_data=[]
        datas = request.data.get('data')
        print('SQL QUERY', datas)
        with connection.cursor() as cursor:
            cursor.execute(datas)
            datafilter = cursor.fetchall()
        json_data = json.dumps(datafilter)
        return Response(json_data)