#include "ed/models/models.h"

#include <tue/filesystem/path.h>
#include <ros/package.h>

#include "shape_loader.h"

#include <tue/config/reader.h>

namespace ed
{

namespace models
{

NewEntityPtr create(const TYPE& type, tue::Configuration cfg, const UUID& id)
{
    NewEntityPtr e;
    tue::filesystem::Path model_path(ros::package::getPath("ed_object_models") + "/models/" + type);

    if (model_path.exists())
    {        
        tue::filesystem::Path model_cfg_path(model_path.string() + "/model.yaml");

        if (model_cfg_path.exists())
        {
            tue::Configuration model_cfg;
            if (model_cfg.loadFromYAMLFile(model_cfg_path.string()))
            {
                //! Check the inheritance
                std::string parent_type;
                if (model_cfg.value("type", parent_type, tue::OPTIONAL))
                    e = create(parent_type, tue::Configuration(), id);
                else
                    e = NewEntityPtr(new NewEntity(id, type));

                //! Check the composition
                if (model_cfg.readArray("composition"))
                {
                    while (model_cfg.nextArrayItem())
                    {
                        std::string child_id, child_type;
                        if (model_cfg.value("type", child_type))
                        {
                            NewEntityPtr child_e;
                            if (model_cfg.value("id", child_id, tue::OPTIONAL))
                                child_e = create(child_type, model_cfg.limitScope(), child_id);
                            else
                                child_e = create(child_type, model_cfg.limitScope());
                            if (child_e)
                                e->children.push_back(child_e);
                        }
                    }

                    model_cfg.endArray();
                }

                //! Set shape
                if (model_cfg.readGroup("shape"))
                {
                    geo::ShapePtr shape = loadShape(model_path.string(), model_cfg.limitScope());
                    if (shape)
                        e->shape = shape; // Overwrite the shape

                    model_cfg.endGroup();
                }

                //! Merge the configs
                e->config.add(model_cfg.data());
                e->config.add(cfg.data());

                tue::config::Reader e_data(e->config);

                //! Set pose
                if (e_data.readGroup("pose"))
                {
                    if (!e_data.value("x", e->pose.t.x) ||
                            !e_data.value("y", e->pose.t.y) ||
                            !e_data.value("z", e->pose.t.z))
                    {
                        std::cout << "ed::models::create() : In model '" << type << "': ERROR loading pose; pose is malformed." << std::cout;
                        std::cout << model_cfg << std::endl;
                    }

                    double X = 0, Y = 0, Z = 0;
                    if (e_data.value("X", X, tue::config::OPTIONAL) |
                        e_data.value("Y", Y, tue::config::OPTIONAL) |
                        e_data.value("Z", Z, tue::config::OPTIONAL))
                    {
                        e->pose.setRPY(X,Y,Z);
                    }

                    e_data.endGroup();
                }
            }
            else
            {
                std::cout << "ed::models::create() : ERROR loading configuration for model '" << type << "'; '" << model_cfg_path.string() << "' failed to parse yaml file." << std::endl;
            }
        }
        else
        {
            std::cout << "ed::models::create() : ERROR loading configuration for model '" << type << "'; '" << model_cfg_path.string() << "' file does not exist." << std::endl;
        }
    }
    else
    {
        std::cout << "ed::models::create() : ERROR loading model '" << type << "'; '" << model_path.string() << "' does not exist." << std::endl;
    }

    return e;
}

}

}
