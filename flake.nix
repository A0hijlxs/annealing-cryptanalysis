{
    description = "annealing-cryptanalysis devshell";

    inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        flake-utils.url = "github:numtide/flake-utils";
    };

    outputs = { self, nixpkgs, flake-utils }:
        flake-utils.lib.eachDefaultSystem (system:
            let
                pkgs = import nixpkgs { inherit system; };
                python = pkgs.python3.withPackages (ps: with ps; [
                    numpy
                    matplotlib
                    pytest
                    marimo
                ]);
            in
                {
                devShells.default = pkgs.mkShell {
                    packages = [ python pkgs.ruff ];

                    shellHook = ''
                        export PYTHONPATH="$PWD/src:$PYTHONPATH"
                        echo "codebreak package is on PYTHONPATH (src/)."
                        echo "Run 'pytest' to run the tests, or 'marimo edit demo.py' to open the demo notebook."
                    '';
                };
            });
}
