#include "polypartition/polypartition.h"

#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>

#include <geolib/Mesh.h>
#include <geolib/Shape.h>
#include <geolib/serialization.h>

#include <iostream>

// ----------------------------------------------------------------------------------------------------

void findContours(const cv::Mat& image, const geo::Vec2i& p, std::vector<geo::Vec2i>& points)
{
    static int dx[4] = {1,  0, -1,  0 };
    static int dy[4] = {0,  1,  0, -1 };

    unsigned char v = image.at<unsigned char>(p.y, p.x);

    int d_current = 0; // Current direction
    int x2 = p.x;
    int y2 = p.y;

    int line_piece_min = 1e9; // minimum line piece length of current line
    int line_piece_max = 0; // maximum line piece length of current line

    int d_main = d_current; // The main direction in which we're heading. If we follow a line
                            // that gradually changes to the side (1-cell side steps), this direction
                            // denotes the principle axis of the line

    points.push_back(p);

    int n_uninterrupted = 1;
    geo::Vec2i p_corner = p;

    while (true)
    {
        bool found = false;
        int d = (d_current + 3) % 4; // check going left first

        for(int i = -1; i < 3; ++i)
        {
            if (image.at<unsigned char>(y2 + dy[d], x2 + dx[d]) == v)
            {
                found = true;
                break;
            }

            d = (d + 1) % 4;
        }

        if (!found)
            return;        

        geo::Vec2i p_current(x2, y2);

        if ((d + 2) % 4 == d_current)
        {
            // 180 degree turn
            points.push_back(p_current);
            d_main = d;
            line_piece_min = 1e9;
            line_piece_max = 0;

        }
        else if (d_current != d_main)
        {
            // Not moving in main direction (side step)

            if (n_uninterrupted > 1)
            {
                // If side step is bigger than 1, it means we have taken a turn.
                // Add the corner to the list and make this our main direction

                points.push_back(p_corner);
                d_main = d_current;
                line_piece_min = 1e9;
                line_piece_max = 0;
            }
        }
        else
        {
            // Moving in main direction (no side step)

            if (d_current != d)
            {
                // Turning 90 degrees

                // Check if the length of the last line piece is OK w.r.t. the other pieces in this line. If it differs to much,
                // (i.e., the contour has taken a different angle), add the last corner to the list. This way, we introduce a
                // bend in the contour
                if (line_piece_max > 0 && (n_uninterrupted < line_piece_max - 2 || n_uninterrupted > line_piece_min + 2))
                {
                    // Line is broken, add the corner as bend
                    points.push_back(p_corner);

                    line_piece_min = 1e9;
                    line_piece_max = 0;
                }

                // Update the line piece lenth boundaries with the current found piece
                line_piece_min = std::min(line_piece_min, n_uninterrupted);
                line_piece_max = std::max(line_piece_max, n_uninterrupted);
            }
        }

        if (d_current != d)
        {
            p_corner = p_current;
            n_uninterrupted = 0;
        }

        ++n_uninterrupted;

        x2 = x2 + dx[d];
        y2 = y2 + dy[d];

        if (x2 == p.x && y2 == p.y)
        {
            if (n_uninterrupted >= 3)
            {
                if (p_corner.x != points.back().x || p_corner.y != points.back().y)
                    points.push_back(p_corner);
            }

            return;
        }

        d_current = d;
    }
}

// ----------------------------------------------------------------------------------------------------

int main(int argc, char **argv)
{
    if (argc <= 1)
        return 0;

    std::string image_filename = argv[1];
    std::cout << "Loading " << image_filename << std::endl;

    cv::Mat image = cv::imread(image_filename, CV_LOAD_IMAGE_GRAYSCALE);   // Read the file

    cv::Mat viz(image.rows, image.cols, CV_8UC3, cv::Scalar(0, 0, 0));
    for(int y = 0; y < image.rows; ++y)
    {
        for(int x = 0; x < image.cols; ++x)
        {
            unsigned char v = image.at<unsigned char>(y, x);
            viz.at<cv::Vec3b>(y, x) = cv::Vec3b(v, v, v);
        }
    }

    if (image.data)
    {
        std::cout << "Successfully loaded" << std::endl;

        cv::Mat vertex_index_map(image.rows, image.cols, CV_32SC1, -1);

        for(int y = 0; y < image.rows; ++y)
        {
            for(int x = 0; x < image.cols; ++x)
            {
                unsigned char v = image.at<unsigned char>(y, x);

                if (v != 255)
                {
                    std::vector<geo::Vec2i> points;
                    findContours(image, geo::Vec2i(x, y), points);

                    int num_points = points.size();

                    std::cout << std::endl << "Total polygon size: " << points.size() << std::endl;

                    if (num_points > 2)
                    {

                        for(unsigned int i = 0; i < num_points; ++i)
                        {
                            int k = (i + 1) % num_points;
                            cv::line(viz, cv::Point(points[i].x, points[i].y),
                                     cv::Point(points[k].x, points[k].y), cv::Scalar(0, 0, 255));
                        }

                        TPPLPoly poly;
                        poly.Init(num_points);

                        geo::Mesh mesh;

                        double min_z = 0;
                        double max_z = 0;

                        for(unsigned int i = 0; i < num_points; ++i)
                        {
                            poly[i].x = points[i].x;
                            poly[i].y = points[i].y;

                            // Convert to world coordinates
                            double wx = points[i].x * 0.025;
                            double wy = points[i].y * 0.025;

                            vertex_index_map.at<int>(points[i].y, points[i].x) = i;

                            mesh.addPoint(geo::Vector3(wx, wy, min_z));
                            mesh.addPoint(geo::Vector3(wx, wy, max_z));
                        }

                        // Calculate side triangles
                        for(int i = 0; i < num_points; ++i)
                        {
                            int j = (i + 1) % num_points;
                            mesh.addTriangle(i * 2, j * 2, i * 2 + 1);
                            mesh.addTriangle(i * 2 + 1, j * 2, j * 2 + 1);
                        }

                        TPPLPartition pp;
                        std::list<TPPLPoly> testpolys, result;
                        testpolys.push_back(poly);

                        if (!pp.Triangulate_EC(&poly, &result))
                        {
                            std::cout << "Error" << std::endl;
                        }
                        else
                        {
                            std::cout << "Number of triangles: " << result.size() << std::endl << std::endl;

                            for(std::list<TPPLPoly>::iterator it = result.begin(); it != result.end(); ++it)
                            {
                                TPPLPoly& cp = *it;

                                int i1 = vertex_index_map.at<int>(cp[0].y, cp[0].x) + 1;
                                int i2 = vertex_index_map.at<int>(cp[1].y, cp[1].x) + 1;
                                int i3 = vertex_index_map.at<int>(cp[2].y, cp[2].x) + 1;

                                mesh.addTriangle(i1, i2, i3);

                                // visualize
                                for(unsigned j = 0; j < cp.GetNumPoints(); ++j)
                                {
                                    int k = (j + 1) % cp.GetNumPoints();
                                    cv::line(viz, cv::Point(cp[j].x, cp[j].y), cv::Point(cp[k].x, cp[k].y), cv::Scalar(0, 0, 255));
                                }
                            }
                        }

                    }

                    cv::floodFill(image, cv::Point(x, y), 255);
                }
            }
        }        

        cv::imshow("image", viz);
        cv::waitKey();
    }
    else
    {
        std::cout << "ed::models::getHeightMapShape() : ERROR loading heightmap at '" << image_filename << "'. Image constains invalid data." << std::endl;
    }
}
