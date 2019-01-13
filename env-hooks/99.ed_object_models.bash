function ed_object_models_setup {
    local model_path=$(rospack find ed_object_models)/models

    local model_paths=($(find $model_path -type f -name '*model*.sdf' | xargs dirname | xargs dirname))
    local unique_model_paths=$(printf "%s\n" "${model_paths[@]}" | sort -ru | tr '\n' ' ')
    local model_paths_string=""
    for dir in $unique_model_paths
    do
        if [[ "$dir" == "$model_path" ]]
        then
            # You want to have the main model path at the end
            continue
        fi
        model_paths_string="${model_paths_string:+${model_paths_string}:}$dir"
    done

    model_paths_string="${model_paths_string:+${model_paths_string}:}$model_path"

    if [ -z $GAZEBO_MODEL_PATH ]
    then
        export GAZEBO_MODEL_PATH=$model_paths_string
    else
        export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$model_paths_string
    fi
    if [ -z $GAZEBO_RESOURCE_PATH ]
    then
        export GAZEBO_RESOURCE_PATH=$model_paths_string
    else
        export GAZEBO_RESOURCE_PATH=$GAZEBO_RESOURCE_PATH:$model_paths_string
    fi
}

ed_object_models_setup
