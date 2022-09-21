function ambientGAN_data
    total_example_number = 2000;
    total_lambda = 1;

    rng('shuffle')


    for example_number = 1:1:total_example_number
        %% Generate skin/vessel properties for tissue model 
        system_volume = ones(1,40,40);
        vess_num=3;
        for j = 1:1:vess_num
        imageSizeX = 40;
        imageSizeY = 40;
        imageSizeZ = 1;
        [X,Y,Z] = ndgrid(1:imageSizeX, 1:imageSizeY, 1:imageSizeZ);
        % Next create the circle in the image.
        radius = randi([3 5],1);
        centerX = randi([radius+1 39-radius],1);
        centerY = randi([radius+1 39-radius],1);
        centerZ = 1;
        
        circlePixels = (Z-centerZ).^2 + (Y-centerY).^2 + (X-centerX).^2 <= radius.^2;
        sphere_indices = find(circlePixels==1);
        system_volume(sphere_indices) = j+1;
        end
    %% Calculate optical parameters for MCXLAB
        %background
        mua_1 = rand(1)*.5;
        mus_1 = 0; %Jacques
        n_1 = 1.4;
        a_1 = 1;
        
        %circle_1
        mua_2 = mua_1 + 1.3*rand(1);
        mus_2 = 0; %Jacques
        n_2 = 1.4;
        a_2 = 1;
        
        %circle_2
        mua_3 = mua_1 + 1.3*rand(1);
        mus_3 = 0; %Jacques
        n_3 = 1.4;
        a_3 = 1;
        
        %circle_3
        mua_4 = mua_1 + 1.3*rand(1);
        mus_4 = 0; %Jacques
        n_4 = 1.4;
        a_4 = 1;



        %% Run MCXLAB for each lambda
        clear cfg cfgs
        cfg.nphoton=(1e7);

        cfg.vol = uint8(system_volume);
        cfg.unitinmm = .1;
        cfg.srcparam1 = [50 0 0 0];
        cfg.srcparam2 = [0 0 0 0];

        cfg.srctype = 'gaussian';
        cfg.srcpos=[0 0 20];
        cfg.srcdir=[0 1 0];
        cfg.gpuid=2;
        cfg.autopilot=1;
        %cfg.prop -> [air (0), epidermis (1), dermis (2), venous_1 (3), venous_2 (4), artery (5), hypodermis (6) ]
        %mu_a and mu_s values are multiplied by 0.1 to convert to mm-1
        cfg.prop=[0 0 1 1; mua_1 mus_1 a_1 n_1; mua_2 mus_2 a_2 n_2; mua_3 mus_3 a_3 n_3; mua_4 mus_4 a_4 n_4; ];

        cfg.tstart=0;
        cfg.tend=1e-9;
        cfg.tstep=1e-11;
        cfg.isreflect=1;
        cfg.isrefint=1;
        % calculate the flux distribution with the given config
        flux=mcxlab(cfg);

        
         

        

        %Calculate fluence by integrating flux overtime
        %This is done by multiple flux by size of timestep and adding them
        %all together
        flux_data = flux(1).data;
        fluence_data = flux_data*cfg.tstep;
        fluence_data = sum(fluence_data,4);
        
        %Absorption coefficient map is generated and stored for future
        %initial pressure calculation
        %values multipled by 0.1 to convert to mm-1
        
        mua_volume = system_volume;
        mua_volume(find(system_volume == 1)) = mua_1;
        mua_volume(find(system_volume == 2)) = mua_2;
        mua_volume(find(system_volume == 3)) = mua_3;
        mua_volume(find(system_volume == 4)) = mua_4;
                
        %Initial pressure calculated
        
        p0_volumes(example_number,:,:,:) = mua_volume.*fluence_data;
        mua_volumes(example_number,:,:,:) =mua_volume;

    end
        %% Save data_files
        save('fluence_train_data.mat', 'p0_volumes','mua_volumes');

end
