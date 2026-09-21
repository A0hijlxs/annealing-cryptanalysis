{
    description = "annealing-cryptanalysis devshell with Jupyter";

    inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        flake-utils.url = "github:numtide/flake-utils";
    };

    outputs = { self, nixpkgs, flake-utils }:
        flake-utils.lib.eachDefaultSystem (system:
            let
                pkgs = import nixpkgs { inherit system; };
                python = pkgs.python3.withPackages (ps: with ps; [
                    jupyterlab
                    numpy
                    pandas
                    matplotlib
                    pycryptodome
                    sympy
                    requests
                    pytest
                ]);
            in
                {
                devShells.default = pkgs.mkShell {
                    packages = [ python ];

                    shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            echo "codebreak package is on PYTHONPATH (src/)."
            echo "Run 'pytest' to run the tests, or 'jupyter lab' to start the notebook server."
                    '';
                };
            });
}
